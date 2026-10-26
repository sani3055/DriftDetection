import fs from 'node:fs/promises';
import {pathToFileURL} from 'node:url';
const runtime='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs';
const {FileBlob,PresentationFile}=await import(pathToFileURL(runtime).href);
const deck=await PresentationFile.importPptx(await FileBlob.load('D:/Downloads/Review 3- 28-10- 2026.pptx'));
console.log((await deck.inspect({kind:'slide,textbox,image,table,layout',maxChars:18000})).ndjson);
console.log('slides',deck.slides.items.map(s=>({id:s.id,shapeCount:s.shapes.items.length,imageCount:s.images.items.length,shapes:s.shapes.items.map(sh=>({id:sh.id,text:String(sh.text),position:sh.position}))})));
await fs.writeFile('D:/Projects/DriftDetection/tmp/review3_ppt/template-proto.json',JSON.stringify(deck.toProto(),null,2));
