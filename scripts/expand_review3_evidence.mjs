import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root='D:/Projects/DriftDetection';
const source=path.join(root,'outputs/Review_3_Capstone_Final.pptx');
const tmp=path.join(root,'tmp/review3_capstone_expanded19');
const final=path.join(root,'outputs/Review_3_Capstone_Expanded_19_Slides.pptx');
const skill='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const runtime='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=path.join(runtime,'node/node_modules');
const {FileBlob,PresentationFile}=await import(pathToFileURL(path.join(runtime,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
await fs.mkdir(tmp,{recursive:true});
const sourceHash=createHash('sha256').update(await fs.readFile(source)).digest('hex');
const deck=await PresentationFile.importPptx(await FileBlob.load(source));
const originals=[...deck.slides.items];
if(originals.length!==15)throw new Error('Expected the reviewed 15-slide source.');
await fs.writeFile(path.join(tmp,'before-inspection.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','layout','title','elements.id','elements.kind','elements.text','notes.text']})).ndjson);
const FONT='Times New Roman';
const BLUE='#4F81BD';
const layout=originals[10].layout;

function box(slide,text,x,y,w,h,pt=22,style={}){
  const sh=slide.shapes.add({geometry:'textbox',name:text.slice(0,50),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  sh.text=text;
  sh.text.style={fontFamily:FONT,typeface:FONT,fontSize:pt*4/3,color:'#000000',bold:false,alignment:'left',verticalAlignment:'top',...style};
  sh.text.insets={left:0,right:0,top:0,bottom:0};
  return sh;
}
function makeSlide(title){
  const slide=deck.slides.add({layoutId:layout.id});
  box(slide,title,88,71.5,1104,65,30,{bold:true});
  box(slide,'28-10-2026',88,667.33,288,38.33,12,{color:'#8B8B8B'});
  box(slide,'SCOPE',424,667.33,432,38.33,12,{color:'#8B8B8B',alignment:'center'});
  box(slide,'0',904,667.33,288,38.33,12,{color:'#8B8B8B',alignment:'right'});
  return slide;
}
function table(slide,values,{y=220,height=300,widths,pt=18,padding=6}={}){
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:88,top:y,width:1104,height,values,columnWidths:widths});
  t.styleOptions={headerRow:true,bandedRows:false};
  t.borders.assign({style:'solid',fill:'#B6BEC8',width:1});
  for(let r=0;r<values.length;r++)for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);
    cell.fill=r===0?BLUE:(r%2?'#E9EDF5':'#D5DFEF');
    cell.text.style={fontFamily:FONT,typeface:FONT,fontSize:pt*4/3,color:r===0?'#FFFFFF':'#000000',bold:r===0,alignment:'left',verticalAlignment:'middle'};
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:9,right:9,top:padding,bottom:padding},anchor:'center'});
  return t;
}
function notes(slide,text,sources){slide.speakerNotes.text=text+'\n\nSources: '+sources.join('; ');}
async function csv(relative){
  const [header,...rows]=(await fs.readFile(path.join(root,relative),'utf8')).trim().split(/\r?\n/).map(s=>s.split(','));
  return rows.map(row=>Object.fromEntries(header.map((key,i)=>[key,row[i]])));
}
const f4=v=>Number(v).toFixed(4);
const f6=v=>Number(v).toFixed(6).replace('-','−');

const protocol=makeSlide('Experimental Protocol and Safeguards');
box(protocol,'The calendar split and controlled scenario tests answer different questions.',88,160,1104,60,22);
table(protocol,[
  ['Part of the evaluation','Protocol'],
  ['Real monthly observations','27 training, 9 validation and 9 test months.\nThe primary records have no attack labels.'],
  ['Controlled scenarios','200-row reference. Seven scenarios.\nMain intervention changes 25% of the rows.'],
  ['Thresholds and held-out tests','5 validation seeds tune thresholds.\n10 separate test seeds give 70 units per policy.'],
  ['Policy comparison','Each run restarts from the baseline.\nPeriodic updates occur every third scenario run.'],
],{y:225,height:330,widths:[345,759],pt:19});
box(protocol,'Changed-row masks enter evaluation only. Fitting and diagnosis do not use them.',88,590,1104,65,20);
notes(protocol,'Distinguish the 27/9/9 chronological partition from the controlled experiment. The controlled reference and current matrices are training-derived samples, not the nine held-out calendar months. Validation seeds are 0–4; test seeds are 5–14. Seven scenarios times ten test seeds produce 70 paired scenario-seed units per policy, not 70 independent real incidents. The intensity 0.25 applies to the primary changed field; a secondary field changes at half that intensity. Every policy/scenario run starts from the baseline. Protected refits use replay plus baseline-normal candidates, minimum 10, with 50 estimators against a 100-estimator baseline. This difference is a limitation, not an additional policy advantage. No real AWS IAM changes are made.',[
  'configs/benchmark.yaml','configs/adaptation.yaml','src/experiments/controlled_benchmark.py','src/adaptation/controller.py','data/processed/temporal_split.json',
]);

const interpretation=makeSlide('Interpreting F1 and Update Rates');
box(interpretation,'Diagnosis and event detection use different targets and different averages.',88,160,1104,60,22);
table(interpretation,[
  ['Reported measure','Meaning'],
  ['Diagnosis macro-F1: 0.7306','Validation performance across three drift classes.\nThis evaluates the dual diagnosis rule.'],
  ['Mean event F1: 0.2873','Dual-policy event-detection F1, averaged over\nall 70 held-out scenario-seed runs.'],
  ['Unnecessary-update rate: 0.0000','Requests in non-security scenarios / all runs.\nZero does not establish complete attack detection.'],
],{y:225,height:270,widths:[400,704],pt:19});
box(interpretation,'Stable and benign scenarios contain no positive targets.\nTheir positive-class F1 is zero under the configured metric.',88,525,1104,85,21);
box(interpretation,'Read the mean F1 together with recall, false-positive rate and update frequency.',88,625,1104,30,18);
notes(interpretation,'Explain the two F1 values before comparing results. Diagnosis macro-F1 0.7306 is selected on validation scenarios and averages the three named window/scenario classes. The coupled validation score uses five labels, so its raw score is not a matched-class comparison. Event-detection F1 is calculated from row masks after prediction and then averaged across scenario-seed runs. Four of the seven scenario families (stable plus three benign changes) have no positive targets. sklearn metrics use zero_division=0, making their positive-class F1 zero even if all negative rows are predicted correctly. This explains part of the low aggregate mean; it does not excuse missed positive rows or establish high security performance. Unnecessary adaptation divides requests in non-security scenarios by all runs, not just requested updates. Report all outcomes, including security recall and benign false positives. Neither F1 value measures verified attack accuracy on the primary unlabelled corpus.',[
  'src/evaluation/metrics.py','src/drift/diagnosis.py','data/benchmark/diagnosis_thresholds.json','data/benchmark/adaptation_summary.csv','data/benchmark/adaptation_results.csv',
]);

const paired=await csv('results/paired_inference.csv');
const stat=makeSlide('Paired Statistical Evidence');
box(stat,'Dual minus static, using the same 70 scenario-seed units for both policies.',88,160,1104,60,22);
const statRows=['false_positive_rate','f1'].map(name=>{
  const r=paired.find(r=>r.metric===name);
  return [name==='f1'?'Mean event F1':'False-positive rate',f6(r.mean_difference),`[${f6(r.ci_low)}, ${f6(r.ci_high)}]`,name==='f1'?Number(r.q_value_bh).toFixed(6):Number(r.q_value_bh).toFixed(7)];
});
table(stat,[['Measure','Mean change','95% bootstrap interval','BH-adjusted q'],...statRows],{y:235,height:190,widths:[240,195,440,229],pt:18});
box(stat,'The FPR interval stays below zero, supporting a reduction in this benchmark.',88,465,1104,65,21);
box(stat,'The F1 interval crosses zero. An F1 improvement is not established.',88,535,1104,65,21);
box(stat,'Shared samples limit independence. These results do not establish operational reliability.',88,625,1104,30,18);
notes(stat,'Mean change is the paired dual-minus-static difference. Negative FPR is preferable. FPR difference −0.08847820375084474 has a bootstrap 95% interval [−0.12723188025721568, −0.05610644872221761]. Wilcoxon p=0.00028961940975555264, BH-adjusted q=0.00043442911463332894. This is about an 8.85 percentage-point reduction, not an 8.85 percent relative reduction. F1 difference −0.002795839473019074 has interval [−0.01809637354175756, 0.011245294444313738] and adjusted q=0.9433920568226558. The interval crossing zero does not prove equivalence or non-inferiority, which would require a margin and a corresponding test. These are repeated controlled scenario-seed units with shared samples, not independently observed real incidents. Coupled, conservative-coupled, SHAP-only and dual policies have identical outcomes in the current controlled benchmark.',[
  'results/paired_inference.csv','src/evaluation/inference.py','data/benchmark/adaptation_results.csv',
]);

const detectors=await csv('data/robustness/detector_ablation_summary.csv');
const robustness=makeSlide('Detector and Sample Size Robustness');
box(robustness,'Separate controlled robustness tests, rather than the policy-comparison averages.',88,160,1104,60,21);
const names={'isolation_forest_100':'Isolation Forest, 100 trees','isolation_forest_200':'Isolation Forest, 200 trees','isolation_forest_50':'Isolation Forest, 50 trees','local_outlier_factor':'Local Outlier Factor','one_class_svm':'One-class SVM'};
table(robustness,[['Detector','Security recall','Security F1','Benign FPR'],...detectors.map(r=>[names[r.detector],f4(r.security_recall),f4(r.security_f1),f4(r.benign_false_positive_rate)])],{y:225,height:285,widths:[380,240,240,244],pt:18});
box(robustness,'One-class SVM has higher recall here, with more benign false positives.',88,540,1104,55,20);
const sizes=await csv('data/robustness/window_size_summary.csv');
box(robustness,'Recall by sample size: '+sizes.map(r=>`${r.sample_size} rows = ${f4(r.security_recall)}`).join('   '),88,605,1104,50,18);
notes(robustness,'This detector-family ablation uses a separate controlled robustness protocol, not the adaptation-policy experiment or the independent labelled corpus. Show security-scenario recall and F1 alongside benign-scenario FPR. The 100-tree Isolation Forest has recall 0.4918, F1 0.6185 and benign FPR 0.0529. One-class SVM reaches recall 0.8080 and F1 0.7917 but benign FPR rises to 0.1301. Do not declare a universally best detector: on independent labelled logs, LOF and Isolation Forest have different rankings and One-class SVM performs poorly. Sample-size recall is non-monotonic (100: 0.0884; 200: 0.4918; 500: 0.4152), so the current experiment does not establish 200 rows as a general optimum. Derivative-feature consistency, unknown-category collapse and matched baseline/refit ensemble sizes remain limitations.',[
  'data/robustness/detector_ablation_summary.csv','data/robustness/window_size_summary.csv','data/robustness/robustness_metadata.json','data/external_validation/external_detector_metrics.csv',
]);

const order=[...originals.slice(0,10),protocol,originals[10],interpretation,stat,robustness,...originals.slice(11)];
deck.slides.reorder(order.map(s=>'sl/'+s.id));
for(const [i,slide] of deck.slides.items.entries()){
  for(const shape of slide.shapes.items){
    if(shape.position.top>660&&shape.position.left>850)shape.text=String(i+1);
  }
}
if(deck.slides.items.length!==19)throw new Error('Expected 19 slides.');
await fs.writeFile(path.join(tmp,'after-inspection.ndjson'),(await deck.inspect({select:'$.slides[*]',include:['id','index','layout','title','elements.id','elements.kind','elements.text','notes.text']})).ndjson);
await (await PresentationFile.exportPptx(deck)).save(path.join(tmp,'candidate.pptx'));
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const tableSlides=[5,6,7,10,11,12,13,14,15,16,18];
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:path.join(tmp,'candidate.pptx'),finalPath:final,
  pythonExecutable:path.join(runtime,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:19,requiredNativeTableOwnerSlides:tableSlides,
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...tableSlides.flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'reference',families:['Times New Roman'],referencePath:source,referenceSha256:sourceHash},
  verifyArtifactToolImport:true,receiptPath:path.join(tmp,`validation-${Date.now()}.json`),
});
if(createHash('sha256').update(await fs.readFile(source)).digest('hex')!==sourceHash)throw new Error('Source deck changed.');
await fs.writeFile(path.join(tmp,'source-preservation.json'),JSON.stringify({source,sourceHash,final,originalSlidePositions:[1,2,3,4,5,6,7,8,9,10,12,16,17,18,19],addedSlides:[11,13,14,15]},null,2));
console.log(JSON.stringify(result));
