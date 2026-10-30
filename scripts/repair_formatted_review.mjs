import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root='D:/Projects/DriftDetection';
const source='D:/Downloads/Review_3_Capstone_Formatted.pptx';
const tmp=path.join(root,'tmp/formatted_review_check');
const final=path.join(root,'outputs/Review_3_Capstone_Formatted_Checked.pptx');
const runtime='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {FileBlob,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
await fs.mkdir(tmp,{recursive:true});
const hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHash=hash(await fs.readFile(source));
const deck=await PresentationFile.importPptx(await FileBlob.load(source));
if(deck.slides.items.length!==19)throw new Error('Unexpected slide count');
await fs.writeFile(path.join(tmp,'before.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','layout','elements.id','elements.text','elements.position','notes.text']})).ndjson);
console.log('Masters',deck.masters.items.length);
function move(slideNumber,prefix,top,height){
  const matches=deck.slides.items[slideNumber-1].shapes.items.filter(s=>String(s.text).startsWith(prefix));
  if(matches.length!==1)throw new Error(`Expected one shape on ${slideNumber}: ${prefix}, found ${matches.length}`);
  const shape=matches[0];
  shape.position={...shape.position,top,height};
}
move(10,'SHAP additivity residual:',615,35);
move(11,'Changed-row masks',565,45);
move(12,'Dual false-positive rate fell',585,75);
move(17,'The primary corpus has no attack labels.',196,325);
move(17,'Cost sensitivity:',535,85);
await fs.writeFile(path.join(tmp,'after.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','layout','elements.id','elements.text','elements.position','notes.text']})).ndjson);
const candidate=path.join(tmp,'candidate.pptx');
await (await PresentationFile.exportPptx(deck)).save(candidate);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
console.log(await finalizePresentation({
  workspaceDir:root,candidatePath:candidate,finalPath:final,
  pythonExecutable:path.join(runtime,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:19,
  requiredNativeTableOwnerSlides:[5,6,7,10,11,12,13,14,15,16,18],
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[5,6,7,10,11,12,13,14,15,16,18].flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'reference',families:['Times New Roman'],referencePath:source,referenceSha256:sourceHash},
  verifyArtifactToolImport:true,receiptPath:path.join(tmp,`validation-${Date.now()}.json`),
}));
if(hash(await fs.readFile(source))!==sourceHash)throw new Error('Source unexpectedly changed');
