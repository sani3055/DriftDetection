import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root='D:/Projects/DriftDetection';
const tmp=path.join(root,'tmp/review3_ppt');
const source='D:/Downloads/Review 3- 28-10- 2026.pptx';
const skill='C:/Users/Lenovo/.codex/plugins/cache/openai-primary-runtime/presentations/26.1025.11240/skills/presentations';
const dependencies='C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies';
process.env.RUNTIME_NODE_MODULES=path.join(dependencies,'node/node_modules');
const {FileBlob,PresentationFile}=await import(pathToFileURL(path.join(dependencies,'node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs')).href);
await fs.mkdir(tmp,{recursive:true});
const deck=await PresentationFile.importPptx(await FileBlob.load(source));
const original=[...deck.slides.items];
const layout=original[10].layout;
const extra=deck.slides.add({layoutId:layout?.id ?? 'p83mt83u'});
deck.slides.reorder([...original.slice(0,11),extra,...original.slice(11)].map(s=>'sl/'+s.id));
const slides=deck.slides.items;
const importedObjects=(await deck.inspect({kind:'image,textbox,shape',maxChars:200000})).ndjson.split('\n').filter(Boolean).map(line=>JSON.parse(line));
const ownedShapes=index=>importedObjects.filter(r=>r.slideIndex===index && ['textbox','shape'].includes(r.kind)).map(r=>({shape:deck.resolve(r.id),aid:r.id}));
const FONT='Times New Roman';
const BLUE='#4F81BD';

function remove(target){deck.delete(target.id.includes('/')?target.id:`${target.constructor.name.toLowerCase().includes('image')?'im':'sh'}/${target.id}`);}
function box(slide,text,x,y,w,h,pt=24,options={}){
  const shape=slide.shapes.add({geometry:'textbox',name:options.name??text.slice(0,45),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  shape.text=text;
  shape.text.style={fontFamily:FONT,typeface:FONT,fontSize:pt*4/3,color:'#000000',bold:false,alignment:'left',verticalAlignment:'top',...options};
  shape.text.insets={left:0,right:0,top:0,bottom:0};
  return shape;
}
function notes(slide,text,sourceFiles=[]){
  slide.speakerNotes.text=text+'\n\nSources: '+sourceFiles.join('; ');
}
function content(slide,lines,pt=26,y=190,h=430){
  const shape=box(slide,'',88,y,1104,h,pt);
  shape.text=lines.map(line=>({runs:[{run:line,style:{typeface:FONT,fontSize:`${pt}pt`}}],spaceAfter:18}));
  return shape;
}
function table(slide,values,{x=88,y=190,width=1104,height=355,widths,pt=20}={}){
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,values,columnWidths:widths});
  t.styleOptions={headerRow:true,bandedRows:false};
  t.borders.assign({style:'solid',fill:'#B6BEC8',width:1});
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);
    cell.fill=r===0?BLUE:(r%2?'#E9EDF5':'#D5DFEF');
    cell.text.style={fontFamily:FONT,typeface:FONT,fontSize:pt*4/3,color:r===0?'#FFFFFF':'#000000',bold:r===0,alignment:'left',verticalAlignment:'middle'};
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:9,right:9,top:7,bottom:7},anchor:'center'});
  return t;
}
const titles=['','Approval Mail From Guide','Aim','Abstract','Literature Review','Research Gap and Novelty','Objectives','Framework / Architecture','Functional Requirements','Modules','Experiments and Results','External Validation','Conclusion and Future Work','Outcome Achieved','References'];

// Preserve the original title slide and logo. Clear only editable source slots.
const cover=slides[0];
for(const image of cover.images.items){if(image.frame.top<0)image.frame={...image.frame,top:0};}
for(const item of ownedShapes(0)) deck.delete(item.aid);
box(cover,'B.Tech. BCSE497J Project-I\nSHAP-Guided Drift Diagnosis for Adaptive\nAnomaly Detection in AWS CloudTrail',200.26,203.06,936.96,114.39,20,{bold:true,alignment:'center'});
box(cover,'Team member\nSANIDHYA BHANDARI (23BCT0029)\n\nFaculty guide\nDr. Badrinath N\n\nReview 3: 28 October 2026',273.92,336.85,742.4,258.35,20,{alignment:'center'});

for(let i=1;i<slides.length;i++){
  const slide=slides[i];
  const shapes=ownedShapes(i);
  const titleShape=shapes.map(r=>r.shape).find(s=>s.position.top<180 && s.position.height>45);
  for(const image of importedObjects.filter(r=>r.slideIndex===i && r.kind==='image')) deck.delete(image.id);
  for(const {shape:sh,aid} of shapes){
    if(sh===titleShape)continue;
    deck.delete(aid);
  }
  if(titleShape){
    titleShape.text=titles[i];
    titleShape.text.style={fontFamily:FONT,typeface:FONT,fontSize:(i===1?28:30)*4/3,bold:true,color:'#000000',alignment:'left'};
    if(i===1||i===13)titleShape.position={left:88,top:71.5,width:1104,height:65};
  }else{
    box(slide,titles[i],48.32,71.5,1104,65,30,{bold:true});
  }
  box(slide,'28-10-2026',88,667.33,288,38.33,12,{color:'#8B8B8B'});
  box(slide,'SCOPE',424,667.33,432,38.33,12,{color:'#8B8B8B',alignment:'center'});
  box(slide,String(i+1),904,667.33,288,38.33,12,{color:'#8B8B8B',alignment:'right'});
}

content(slides[1],[
  'Faculty guide: Dr. Badrinath N',
  'Approval email: not attached to the supplied files',
  'The guide’s email should cover the report, slides, demo and project outcome.',
],26);
notes(slides[1],'The template requires actual guide approval. No approval email was supplied. Replace this status with the authentic email before presenting if it is available. Do not show the sample approval screenshot as proof.');

content(slides[2],[
  'To decide when to update an anomaly detector as CloudTrail activity changes.',
  'Use changes in data and model explanations together.',
  'Reduce model updates that do not help.',
  'Check the approach with controlled tests and a separate dataset.',
],26);
notes(slides[2],'Drift means that data changes over time. Adaptation means updating or retraining the detector. The method uses available observations and model explanations, while labels remain part of evaluation.', ['docs/research_gap.md','docs/capstone_report_content.md']);

content(slides[3],[
  'CloudTrail records actions made in an AWS account.',
  'Normal changes can make an old model raise unwanted alerts.',
  'Isolation Forest finds unusual actions. SHAP explains the model output.',
  'We compare data changes and explanation changes before updating the model.',
  'Data: 1,939,207 records across 45 months. The original data has no attack labels.',
],24);
notes(slides[3],'The source has 18 columns and 45 monthly windows. The calendar split is 27 training, 9 validation and 9 test months. Controlled scenario validation/test seeds are a different protocol from those calendar partitions. Real-data findings are observational.', ['data_manifest/real_cloudtrail_manifest.json','data/processed/temporal_split.json']);

table(slides[4],[
  ['Paper','Objective','Method','Strength / limit','Finding'],
  ['Sethi &\nKantardzic, 2017','Find drift without labels','Unlabelled drift monitoring','Input changes can over-alert','Check model relevance'],
  ['Han et al.\n2023','Handle changes in normal behaviour','OWAD','Security focus\nDifferent data','Adaptation needs care'],
  ['Lee et al.\n2023','Monitor model drift','SHAP-based monitoring','Uses explanations\nDifferent setting','SHAP drift already exists'],
  ['Varma & Ramya\n2025','Explain CloudTrail anomalies','ML and explanations','CloudTrail focus\nNo coupling gate','Supports the use case'],
],{height:430,widths:[195,210,220,255,224],pt:18});
notes(slides[4],'Core literature only. This is not a claim that the separate 100-record PRISMA collection is a completed systematic review. Sethi and Kantardzic DOI 10.1016/j.eswa.2017.04.008; Han et al. DOI 10.14722/ndss.2023.24830; Lee et al. DOI 10.32604/cmc.2023.040235; Varma and Ramya DOI 10.1109/ICNGN67480.2025.11413642.', ['docs/literature_matrix.csv']);

box(slides[5],'A data change alone does not tell us whether the model needs an update.',88,173,1104,68,24);
table(slides[5],[
  ['Observed change','Possible meaning'],
  ['Data changes, explanations stay similar','Likely routine change'],
  ['Both change on the same features','May need a model update'],
  ['Signals disagree','Needs closer review'],
],{y:265,height:245,widths:[590,514],pt:22});
box(slides[5],'New part: coupling checks whether the same features drive both changes.',88,545,1104,75,24,{bold:true});
notes(slides[5],'Coupling is cosine similarity between per-feature PSI and absolute SHAP displacement on five shared categorical features. A conservative variant also uses centred alignment. These mathematical tools are established. The contribution is their CloudTrail-specific integration and evaluation. High coupling does not confirm an attack. Current controlled results are neutral relative to the simpler dual rule.', ['docs/attribution_feature_coupling.md','src/drift/drift_monitor.py']);

content(slides[6],[
  'Prepare the data in time order and train the detector.',
  'Track changes in data and SHAP explanations.',
  'Compare update rules and count unnecessary updates.',
  'Test the method on a separate cloud-log dataset.',
],26,174,360);
box(slides[6],'SDG 9: reliable digital infrastructure\nSDG 16: accountable security decisions',88,550,1104,78,20);
notes(slides[6],'SDG links describe the project’s intended relevance, not measured social impact. The capstone outcome is a working research prototype, code, evaluation artifacts and report.', ['docs/capstone_report_content.md']);

// Editable block diagram required by the Review 3 architecture section.
function block(text,x,y,w=245,h=100){
  const sh=slides[7].shapes.add({geometry:'rect',name:text,position:{left:x,top:y,width:w,height:h},fill:'#F1F5FB',line:{fill:BLUE,width:1.5}});
  sh.text=text;sh.text.style={fontFamily:FONT,typeface:FONT,fontSize:22*4/3,color:'#000000',alignment:'center',verticalAlignment:'middle'};return sh;
}
function arrow(x,y,w=40,h=24){slides[7].shapes.add({geometry:'rightArrow',name:'Flow connector',position:{left:x,top:y,width:w,height:h},fill:BLUE,line:{fill:BLUE,width:0}});}
block('CloudTrail\nlogs',88,205);block('Prepare\nfeatures',375,205);block('Isolation Forest\nscores',662,205);block('SHAP\nexplanations',949,205);
arrow(337,243,34);arrow(624,243,34);arrow(911,243,34);
slides[7].shapes.add({geometry:'downArrow',name:'Explanations to drift measurement',position:{left:1060,top:312,width:24,height:28},fill:BLUE,line:{fill:BLUE,width:0}});
slides[7].shapes.add({geometry:'leftArrow',name:'Continue to the drift stage',position:{left:255,top:346,width:830,height:20},fill:BLUE,line:{fill:BLUE,width:0}});
slides[7].shapes.add({geometry:'downArrow',name:'Enter drift measurement',position:{left:245,top:373,width:20,height:27},fill:BLUE,line:{fill:BLUE,width:0}});
block('Feature drift and SHAP drift',88,405,335,105);block('Coupling and\ndiagnosis',473,405,335,105);block('Protected\nmodel update',858,405,335,105);
arrow(430,445,34);arrow(815,445,34);
box(slides[7],'The model uses past data plus current rows it predicts as normal for a requested update.',88,555,1104,65,22);
notes(slides[7],'The top row produces detector and explanation evidence. The lower row measures changes and applies the selected update rule. The pipeline is offline and does not change IAM policies or deploy AWS resources. A protected update uses replay data plus baseline-normal candidates, with a minimum candidate count of 10. Each controlled run starts from the baseline, rather than a persistent online model.', ['src/adaptation/controller.py','scripts/run_all.py']);

content(slides[8],[
  'Read the source data without changing it.',
  'Learn feature codes from training data only.',
  'Save anomaly scores, explanations and drift signals.',
  'Apply the same update rules to each test scenario.',
  'Save results so they can be checked and repeated.',
],26);
notes(slides[8],'The seven detector inputs are eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and derived isRoot. Unknown categorical values map to -1. The main export has month-level time, limiting event-sequence analysis.', ['src/features/event_features.py','configs/model.yaml']);

table(slides[9],[
  ['Module','What it does'],
  ['Data preparation','Checks the source and builds monthly windows'],
  ['Detection and explanation','Finds unusual events and computes SHAP values'],
  ['Drift and coupling','Compares data changes with explanation changes'],
  ['Adaptation','Decides whether to refit the model'],
  ['Evaluation','Compares rules and saves results'],
],{height:365,widths:[360,744],pt:22});
notes(slides[9],'Implementation modules: src/features/event_features.py; src/explain/shap_explainer.py; src/drift/drift_monitor.py; src/drift/diagnosis.py; src/adaptation/controller.py; src/evaluation/metrics.py. This slide describes the current repository rather than the earlier cloud-remediation backend.', ['src','README.md']);

table(slides[10],[
  ['Update rule','Mean F1','False-positive rate','Unnecessary updates'],
  ['No update','0.2901','0.4282','0.0000'],
  ['Periodic','0.2888','0.3160','0.2000'],
  ['Data change only','0.2734','0.1825','0.3286'],
  ['SHAP change only','0.2873','0.3397','0.0000'],
  ['Dual signals','0.2873','0.3397','0.0000'],
  ['Coupling','0.2873','0.3397','0.0000'],
],{height:340,widths:[340,190,280,294],pt:20});
box(slides[10],'Dual signals reduced false positives versus no update.\nCoupling matched the simpler rules. F1 did not show a clear improvement.',88,560,1104,75,22);
notes(slides[10],'Controlled benchmark only: 7 scenario families times 10 held-out seeds gives 70 paired scenario-seed units per policy. Five separate validation seeds tune thresholds. Dual validation diagnosis macro-F1 is 0.7306. The paired dual-minus-static FPR difference is -0.088478, 95% CI [-0.127232,-0.056106], BH q=0.000434. Paired F1 difference is -0.002796 with CI [-0.018096,0.011245]. The interval crosses zero. Unnecessary update rate uses all evaluated runs as denominator. Coupling and SHAP-only match dual under current settings, including the conservative-coupling ablation. These are not attack metrics on the primary unlabelled corpus.', ['results/adaptation_summary.csv','results/paired_inference.csv','data/benchmark/diagnosis_thresholds.json']);

box(slides[11],'Separate dataset: 24,087 test events\nIsolation Forest event-detection F1: 0.4519',88,170,1104,95,24);
box(slides[11],'Small drift check: 12 windows',88,286,1104,45,24,{bold:true});
table(slides[11],[
  ['Rule','Recall','F1','False-positive rate'],
  ['Dual signals','1.0000','0.9524','0.5000'],
  ['Coupling: source threshold','0.1000','0.1818','0.0000'],
  ['Coupling: target threshold','1.0000','1.0000','0.0000'],
],{y:350,height:210,widths:[510,160,160,274],pt:19});
box(slides[11],'No attack labels used for the new threshold. More tests are needed.',88,620,1104,35,21);
notes(slides[11],'Keep the two evaluation units separate. Detector-only evaluation uses 16,495 benign training and 24,087 mixed test records (2,585 attack-labelled, 21,502 benign). The temporal checkpoint uses 12 scenario windows, including 10 security and 2 benign windows. Feature-only, SHAP-only and dual match. Source coupling transferred poorly. Unsupervised largest-gap calibration selects 0.4990795305 from target conservative scores after source-locked feature/SHAP gates. It uses the evaluated target batch, so this is exploratory transductive calibration, not prospective validation or full post-adaptation recovery.', ['data/external_validation/external_validation_manifest.json','data/external_validation/external_detector_metrics.csv','data/external_validation/external_temporal_diagnosis_metrics.json','docs/unsupervised_transfer_calibration.md']);

content(slides[12],[
  'The working prototype connects drift checks, explanations and model updates.',
  'Controlled tests show fewer false positives than the fixed model.',
  'Coupling needs more evidence of an extra benefit.',
  'Next: test more real changes and longer update sequences.',
],26);
notes(slides[12],'Do not claim coupling superiority or general reliability from the current results. The primary corpus has no attack labels. Controlled perturbations and target-batch calibration have specific limitations. Future work includes consistent derived features, matched-size refits and independent temporal recovery.', ['LIMITATIONS.md','docs/next_experiments.md']);

content(slides[13],[
  'Working Python pipeline with saved results and figures.',
  '28 automated tests pass.',
  'Capstone report and reproducible project code are ready.',
  'Demo: inspect the data, drift signals and update decisions.',
  'Journal work: research draft prepared. No acceptance claimed.',
],24,180,375);
box(slides[13],'github.com/sani3055/DriftDetection',88,575,1104,45,22);
notes(slides[13],'Demonstration path: manifest and temporal split; model feature contract; score and SHAP samples; monthly drift and coupling CSVs; controlled diagnosis and adaptation rows; independent transfer metrics. Commands: python scripts/run_all.py; python scripts/run_external_temporal_diagnosis.py; python -m pytest tests -q. A fresh run on 27 October 2026 passed all 28 tests. The source CSV is external and required for full regeneration. A 100-record literature collection is not a finished PRISMA review. Publication, patent, outcome-form submission and supervisor approval are not established by this presentation.', ['docs/final_validation.md','README.md','outputs/BCSE497J_Capstone_Report_Final.docx']);

content(slides[14],[
  '[1] Liu, Ting and Zhou. Isolation Forest. IEEE ICDM, 2008.',
  '[2] Lundberg and Lee. A Unified Approach to Interpreting Model Predictions. NeurIPS, 2017.',
  '[3] Sethi and Kantardzic. Reliable detection of concept drift from unlabelled data. ESWA, 2017.',
  '[4] Han et al. Normality Shift Detection, Explanation and Adaptation. NDSS, 2023.',
  '[5] Lee et al. Explainable model drift detection in unsupervised settings. CMC, 2023.',
  '[6] AWS CloudTrail and SageMaker feature-attribution documentation.',
],20,172,455);
notes(slides[14],'Full sources: [1] https://doi.org/10.1109/ICDM.2008.17 [2] https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html [3] https://doi.org/10.1016/j.eswa.2017.04.008 [4] https://doi.org/10.14722/ndss.2023.24830 [5] https://doi.org/10.32604/cmc.2023.040235 [6] https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html and https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-monitor-feature-attribution-drift.html. Slide literature also uses Varma and Ramya: https://doi.org/10.1109/ICNGN67480.2025.11413642.', ['docs/literature_matrix.csv']);

await (await PresentationFile.exportPptx(deck)).save(path.join(tmp,'candidate.pptx'));
await fs.writeFile(path.join(tmp,'authored-inspection.ndjson'),(await deck.inspect({kind:'slide,textbox,table',maxChars:80000})).ndjson);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const final=path.join(root,'outputs/Review_3_Final_SHAP_CloudTrail.pptx');
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:path.join(tmp,'candidate.pptx'),finalPath:final,
  pythonExecutable:path.join(dependencies,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:15,requiredNativeTableOwnerSlides:[5,6,10,11,12],
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[5,6,10,11,12].flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'reference',families:['Times New Roman','Calibri'],referencePath:source,referenceSha256:createHash('sha256').update(await fs.readFile(source)).digest('hex')},
  verifyArtifactToolImport:true,receiptPath:path.join(tmp,`validation-${Date.now()}.json`),
});
console.log(JSON.stringify(result));
