import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root='D:/Projects/DriftDetection';
const source='D:/Downloads/Review_3_23BCT0029.pptx';
const tmp=path.join(root,'tmp/review_simple_summary');
const final=path.join(root,'outputs/Review_3_23BCT0029_Simplified.pptx');
const runtime='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const skill='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {FileBlob,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
const {finalizePresentation,makeNativeBulletParagraphs}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const hash=b=>createHash('sha256').update(b).digest('hex');
const sourceHash=hash(await fs.readFile(source));
const deck=await PresentationFile.importPptx(await FileBlob.load(source));
if(deck.slides.items.length!==19)throw new Error('Expected 19 source slides');
await fs.writeFile(path.join(tmp,'before.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','elements.id','elements.kind','elements.text','elements.position','notes.text']})).ndjson);
const summary=deck.slides.items[13];
const elements=(await deck.inspect({select:'$.slides[13].elements[*]',include:['id','kind','text','position']})).records;
const title=elements.find(e=>e.text==='Paired Statistical Evidence');
if(!title)throw new Error('Source slide 14 title not found');
deck.resolve(title.id).text.replace('Paired Statistical Evidence','What We Learned from the Tests');
for(const element of elements){
  const footer=element.position?.top>650;
  if(element.id!==title.id&&!footer)deck.delete(element.id);
}
const bullets=[
  'Using data drift and SHAP drift together reduced false alarms in controlled tests.',
  'We did not establish an overall detection improvement. Coupling matched simpler update rules.',
  'Other detectors showed a trade-off between catching simulated changes and raising false alarms.',
  'Larger samples did not always give better results.',
  'On separate cloud logs, the original coupling threshold missed many security windows.',
  'Recalibrating on that batch worked better. Future unseen data still needs testing.',
];
const body=summary.shapes.add({geometry:'textbox',name:'Plain-English test findings',position:{left:88,top:157,width:1104,height:455},fill:'none',line:{fill:'none',width:0}});
body.text=makeNativeBulletParagraphs(bullets,{marginLeftPoints:18,hangingPoints:9,spaceAfterPoints:14});
body.text.style={fontFamily:'Times New Roman',typeface:'Times New Roman',fontSize:20*4/3,color:'#000000',bold:false,alignment:'left',verticalAlignment:'top',autoFit:'none'};
body.text.insets={left:0,right:0,top:0,bottom:0};
summary.speakerNotes.text='Combines the former statistical, robustness and external-validation slides in plain English. Dual signals reduced false-positive rate relative to static in paired controlled tests, but an F1 improvement was not established. Coupling, conservative coupling, SHAP-only and dual policies matched in this benchmark. Detector and sample-size robustness used a different protocol. The external source threshold missed most security windows. Target calibration used the same current target batch, so it is transductive and does not establish future recovery or production readiness.\n\nSources: results/paired_inference.csv; data/benchmark/adaptation_summary.csv; data/robustness/detector_ablation_summary.csv; data/robustness/window_size_summary.csv; data/external_validation/external_temporal_diagnosis_metrics.json; data/external_validation/external_temporal_diagnosis_manifest.json. Independent corpus [13]: https://github.com/ArielCyber/cloud_log_sampling';
deck.slides.keep(Array.from({length:19},(_,i)=>i).filter(i=>i!==14&&i!==15));
for(const [i,slide] of deck.slides.items.entries()){
  for(const shape of slide.shapes.items){
    if(shape.position.top>650&&shape.position.left>850&&/^\d+$/.test(String(shape.text).trim()))shape.text=String(i+1);
  }
}
if(deck.slides.items.length!==17)throw new Error('Expected 17 final slides');
await fs.writeFile(path.join(tmp,'after.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','elements.text','notes.text']})).ndjson);
await (await PresentationFile.exportPptx(deck)).save(path.join(tmp,'candidate.pptx'));
const tables=[5,6,7,10,11,12,13,16];
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:path.join(tmp,'candidate.pptx'),finalPath:final,
  pythonExecutable:path.join(runtime,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:17,requiredNativeTableOwnerSlides:tables,
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--validate-bullet-geometry',...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'reference',families:['Times New Roman'],referencePath:source,referenceSha256:sourceHash},
  verifyArtifactToolImport:true,receiptPath:path.join(tmp,`validation-${Date.now()}.json`),
});
if(hash(await fs.readFile(source))!==sourceHash)throw new Error('Source changed');
console.log(JSON.stringify({final:result.finalPath,sha256:result.finalSha256,slides:17}));
