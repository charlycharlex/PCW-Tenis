// Convierte las texturas JPEG de 1K y 2K (escaneo y suela con firmas) a KTX2 (Basis ETC1S, con mipmaps).
//
// Uso (una vez: npm install dentro de fuentes/ktx2; no hace falta nada más):
//   cd fuentes\ktx2
//   npm install --ignore-scripts
//   node codificar.mjs                 → todas las que falten o sean más viejas que su JPEG
//   node codificar.mjs plateado_izq    → solo las de ese tenis (y vuelve a hacerlas)
//
// Por qué KTX2: subir un JPEG 2K a la GPU congela la página 15–60 ms (hay que pasarlo a RGBA y generar
// mipmaps); un KTX2 llega ya comprimido para la tarjeta, con sus mipmaps, y sube en menos de 1 ms. En la
// GPU ocupa 4–8 veces menos. Lo decodifica (transcodifica) un worker, fuera del hilo principal.
// Por qué ETC1S calidad 128: comparado de cerca contra el JPEG en las firmas, el cromo y el rosa, no se
// distingue; pesa igual que el JPEG en 1K y ~20% más en 2K. UASTC se ve igual y pesa 7–10 veces más.
// La 4K se queda en JPEG: este codificador no acepta más de 12 Mpx (una 4K son 16.7) y solo se usa de
// cerca, en escritorio, y se sube con la escena quieta.
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import jpeg from 'jpeg-js';
import { encodeToKTX2 } from 'ktx2-encoder';

const TEX = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..', 'modelos', 'tex');
const solo = process.argv[2];
const OPCIONES = {
  isUASTC: false, qualityLevel: 128, compressionLevel: 2, enableDebug: false,
  generateMipmap: true, isSetKTX2SRGBTransferFunc: true, isPerceptual: true,
  // la textura del escaneo sigue la convención de UV de glTF (primera fila arriba), igual que KTX2: sin voltear
  imageDecoder: async (buf) => {
    const r = jpeg.decode(buf, { useTArray: true, formatAsRGBA: true, maxMemoryUsageInMB: 2048 });
    return { data: new Uint8Array(r.data.buffer), width: r.width, height: r.height };
  },
};

const jpgs = fs.readdirSync(TEX).filter(f => /_(1k|2k)\.jpg$/.test(f) && (!solo || f.startsWith(solo + '_')));
let hechas = 0;
for (const f of jpgs) {
  const origen = path.join(TEX, f), destino = origen.replace(/\.jpg$/, '.ktx2');
  if (!solo && fs.existsSync(destino) && fs.statSync(destino).mtimeMs > fs.statSync(origen).mtimeMs) continue;
  const t0 = Date.now();
  const ktx = await encodeToKTX2(new Uint8Array(fs.readFileSync(origen)), OPCIONES);
  fs.writeFileSync(destino, ktx);
  hechas++;
  console.log(`${f.padEnd(28)} ${(fs.statSync(origen).size / 1024).toFixed(0).padStart(5)} KB jpg → ${(ktx.length / 1024).toFixed(0).padStart(5)} KB ktx2  (${((Date.now() - t0) / 1000).toFixed(1)} s)`);
}
console.log(hechas ? `listo: ${hechas} texturas` : 'nada que hacer: todas al día');
