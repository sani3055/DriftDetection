import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';

const root='D:/Projects/DriftDetection';
const tmp=path.join(root,'tmp/review3_capstone_final');
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
function table(slide,values,{x=88,y=190,width=1104,height=355,widths,pt=20,padding=7}={}){
  const t=slide.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width,height,values,columnWidths:widths});
  t.styleOptions={headerRow:true,bandedRows:false};
  t.borders.assign({style:'solid',fill:'#B6BEC8',width:1});
  for(let r=0;r<values.length;r++) for(let c=0;c<values[0].length;c++){
    const cell=t.getCell(r,c);
    cell.fill=r===0?BLUE:(r%2?'#E9EDF5':'#D5DFEF');
    cell.text.style={fontFamily:FONT,typeface:FONT,fontSize:pt*4/3,color:r===0?'#FFFFFF':'#000000',bold:r===0,alignment:'left',verticalAlignment:'middle'};
  }
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({margins:{left:9,right:9,top:padding,bottom:padding},anchor:'center'});
  return t;
}
const titles=['','Guide Approval and Project Context','Aim and Scope','Abstract and Dataset','Literature Survey 1: Drift and Adaptation','Research Gap and Novelty','Objectives and Evaluation Plan','Framework / Architecture','Functional Requirements and Inputs','Inputs and Implementation Modules','Experiments and Results','External Validation','Conclusion and Future Work','Outcome Achieved and Demo','References'];

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

box(slides[1],'Faculty guide: Dr. Badrinath N\nGuide approval email: copy not attached',88,170,1104,100,24);
box(slides[1],'Project context',88,305,1104,40,24,{bold:true});
content(slides[1],[
  'Capstone course: BCSE497J Project-I, B.Tech. CSE with IoT specialisation.',
  'Current focus: drift diagnosis and selective updates for an anomaly detector.',
  'Data continuity: the same CloudTrail corpus as the earlier project.',
  'Deliverables: working code, experiments, report and project demonstration.',
  'Final review: 28 October 2026.',
],22,355,230);
box(slides[1],'The guide’s approval email should cover the report, slides, demo and project outcome.',88,600,1104,50,20);
notes(slides[1],'The template requires actual guide approval. No approval email was supplied. Replace this status with the authentic email before presenting if it is available. Do not show the sample approval screenshot as proof.');

box(slides[2],'Aim',88,170,1104,38,24,{bold:true});
box(slides[2],'To decide when an AWS CloudTrail anomaly detector needs an update by comparing changes in its input data with changes in its SHAP explanations.',88,218,1104,105,24);
box(slides[2],'Scope',88,345,1104,38,24,{bold:true});
content(slides[2],[
  'Build an unsupervised detector from historical cloud activity.',
  'Separate routine changes from changes that affect the model’s decisions.',
  'Compare update rules and reduce unnecessary retraining.',
  'Evaluate the method through controlled tests and independent cloud logs.',
],22,395,180);
box(slides[2],'The implementation runs locally. Model-update decisions are recorded for review.',88,600,1104,50,20);
notes(slides[2],'Drift means that data changes over time. Adaptation means updating or retraining the detector. The method uses available observations and model explanations, while labels remain part of evaluation.', ['docs/research_gap.md','docs/capstone_report_content.md']);

content(slides[3],[
  'CloudTrail records AWS API calls, services, regions and identity details.',
  'New workloads and normal behaviour changes can increase false alarms.',
  'Isolation Forest [9] scores unusual events. SHAP [10] explains the model output.',
  'The framework measures data drift, explanation drift and their feature-level coupling.',
],22,170,195);
box(slides[3],'Dataset and time split',88,390,1104,40,24,{bold:true});
box(slides[3],'1,939,207 records, 18 source columns and 45 monthly windows\nFebruary 2017 to October 2020\n27 training months, 9 validation months and 9 held-out test months',88,438,1104,115,22);
box(slides[3],'The original corpus has no attack labels. Real months show observed change; controlled scenarios provide separate evaluation targets.',88,585,1104,65,20);
notes(slides[3],'The source has 18 columns and 45 monthly windows. The calendar split is 27 training, 9 validation and 9 test months. Controlled scenario validation/test seeds are a different protocol from those calendar partitions. Real-data findings are observational.', ['data_manifest/real_cloudtrail_manifest.json','data/processed/temporal_split.json']);

table(slides[4],[
  ['Paper','Objective','Method','Limit / scope','Project response'],
  ['[1] Kuppa &\nLe-Khac, 2022','Detect security\ndrift','Drift detector and\nrecursive updates','Security datasets.\nDifferent protocol.','Combine input\nand SHAP drift.'],
  ['[2] Han et al.\n2023','Handle normality\nshifts','OWAD detects and\nadapts normality','Deep security models.\nDifferent datasets.','Test lightweight\nCloudTrail models.'],
  ['[3] Lee et al.\n2023','Monitor drift\nwithout labels','SHAP-based drift\nsuspicion metric','DGA data.\nNo CloudTrail test.','Compare SHAP drift\nwith input drift.'],
  ['[4] Li et al.\n2024','Use drift type\nfor adaptation','Learn drift type\nand change point','Needs supervised\ndrift-type training.','Use unlabelled\nruntime evidence.'],
],{y:170,height:355,widths:[195,190,245,250,224],pt:18});
box(slides[4],'Main lesson: drift detection, explanation and adaptation already exist.\nOur question is whether feature-level coupling improves CloudTrail update decisions.',88,590,1104,65,18);
notes(slides[4],'Selected core comparators, not a completed 100-paper systematic review. J means journal and C means conference. [1] Aditya Kuppa and Nhien-An Le-Khac, Learn to Adapt: Robust Drift Detection in Security Domain, Computers and Electrical Engineering 102, 108239 (2022). https://doi.org/10.1016/j.compeleceng.2022.108239 [2] Dongqi Han and colleagues, Anomaly Detection in the Open World: Normality Shift Detection, Explanation, and Adaptation, NDSS 2023. https://www.ndss-symposium.org/ndss-paper/anomaly-detection-in-the-open-world-normality-shift-detection-explanation-and-adaptation/ [3] Yongsoo Lee, Yeeun Lee, Eungyu Lee and Taejin Lee, Explainable Artificial Intelligence-Based Model Drift Detection Applicable to Unsupervised Environments, CMC 76(2), 1701–1719 (2023). https://www.techscience.com/cmc/v76n2/54010 [4] Jinpeng Li, Hang Yu, Zhenyu Zhang, Xiangfeng Luo and Shaorong Xie, Concept Drift Adaptation by Exploiting Drift Type, ACM TKDD 18(4), article 96 (2024). https://doi.org/10.1145/3638777 The project-response column states our design choice. It does not claim direct benchmark superiority over these papers.', ['docs/literature_matrix.csv','docs/review3_literature_evidence.md']);

box(slides[5],'Gap: a change in input data does not show how much the detector is affected.\nOur method compares each feature’s data shift with its SHAP attribution shift.',88,165,1104,105,22);
table(slides[5],[
  ['Observed change','Possible meaning'],
  ['Little change in data and explanations','Stable period'],
  ['Data changes, explanations stay similar','Likely routine change'],
  ['Both change on the same features','May need a model update'],
  ['Only explanations change, or signals disagree','Model instability or closer review'],
],{y:295,height:245,widths:[590,514],pt:20});
box(slides[5],'Coupling score: cosine similarity between feature-drift scores and SHAP displacement.\nA high score means the changes line up on the same features. Magnitude thresholds still apply.',88,560,1104,95,20);
notes(slides[5],'Coupling is cosine similarity between per-feature PSI and absolute SHAP displacement on five shared categorical features. A conservative variant also uses centred alignment. These mathematical tools are established. The contribution is their CloudTrail-specific integration and evaluation. High coupling does not confirm an attack. Current controlled results are neutral relative to the simpler dual rule.', ['docs/attribution_feature_coupling.md','src/drift/drift_monitor.py']);

content(slides[6],[
  'Audit the dataset, record its checksum and preserve time order.',
  'Train Isolation Forest and verify that SHAP explanations match its output.',
  'Measure feature drift, explanation drift and coupling across windows.',
  'Test stable, routine-change and security-related scenarios.',
  'Compare no update, periodic, single-signal, dual-signal and coupling rules.',
  'Check how the method behaves on a separate labelled cloud-log dataset.',
],22,170,285);
box(slides[6],'Evaluation measures',88,475,1104,38,23,{bold:true});
box(slides[6],'Precision, recall, F1, false-positive rate, update frequency and unnecessary updates.\nUse paired comparisons and confidence intervals to judge differences.',88,520,1104,70,20);
box(slides[6],'SDG 9: reliable digital infrastructure. SDG 16: accountable security decisions.',88,620,1104,30,18);
notes(slides[6],'SDG links describe the project’s intended relevance, not measured social impact. The capstone outcome is a working research prototype, code, evaluation artifacts and report.', ['docs/capstone_report_content.md']);

// Editable block diagram required by the Review 3 architecture section.
function block(text,x,y,w=245,h=100){
  const sh=slides[7].shapes.add({geometry:'rect',name:text,position:{left:x,top:y,width:w,height:h},fill:'#F1F5FB',line:{fill:BLUE,width:1.5}});
  sh.text=text;sh.text.style={fontFamily:FONT,typeface:FONT,fontSize:22*4/3,color:'#000000',alignment:'center',verticalAlignment:'middle'};return sh;
}
function arrow(x,y,w=40,h=24){slides[7].shapes.add({geometry:'rightArrow',name:'Flow connector',position:{left:x,top:y,width:w,height:h},fill:BLUE,line:{fill:BLUE,width:0}});}
block('CloudTrail\nlogs',88,205);block('Prepare\nfeatures',375,205);block('Isolation Forest\nscores',662,205);block('SHAP\nexplanations',949,205);
box(slides[7],'Baseline: 100 trees, contamination 0.05, seed 42 and seven inputs. Training-only maps.',88,155,1104,35,20);
arrow(337,243,34);arrow(624,243,34);arrow(911,243,34);
slides[7].shapes.add({geometry:'downArrow',name:'Explanations to drift measurement',position:{left:1060,top:312,width:24,height:28},fill:BLUE,line:{fill:BLUE,width:0}});
slides[7].shapes.add({geometry:'leftArrow',name:'Continue to the drift stage',position:{left:255,top:346,width:830,height:20},fill:BLUE,line:{fill:BLUE,width:0}});
slides[7].shapes.add({geometry:'downArrow',name:'Enter drift measurement',position:{left:245,top:373,width:20,height:27},fill:BLUE,line:{fill:BLUE,width:0}});
block('Feature drift and SHAP drift',88,405,335,105);block('Coupling and\ndiagnosis',473,405,335,105);block('Protected\nmodel update',858,405,335,105);
arrow(430,445,34);arrow(815,445,34);
box(slides[7],'When an update is requested, combine past rows with current rows predicted normal.\nRequire at least 10 normal candidates, then fit a 50-tree model and measure the result.',88,550,1104,100,20);
notes(slides[7],'The top row produces detector and explanation evidence. The lower row measures changes and applies the selected update rule. The pipeline is offline and does not change IAM policies or deploy AWS resources. A protected update uses replay data plus baseline-normal candidates, with a minimum candidate count of 10. Each controlled run starts from the baseline, rather than a persistent online model.', ['src/adaptation/controller.py','scripts/run_all.py']);

box(slides[8],'Seven model inputs',88,170,500,40,23,{bold:true});
box(slides[8],'eventName\neventSource\nawsRegion\nuserIdentitytype\nerrorCode\nrequestParametersinstanceType\nisRoot (derived flag)',88,225,500,245,21);
box(slides[8],'Input handling',88,500,500,36,22,{bold:true});
box(slides[8],'Fit category maps on training data.\nUse −1 for unseen categories.\nDerive the root flag from identity type.',88,545,500,100,20);
box(slides[8],'System requirements',650,170,542,40,23,{bold:true});
box(slides[8],'Read the source without changing it.\n\nKeep training and later months separate.\n\nSave anomaly scores and SHAP values.\n\nMeasure drift and log each update decision.\n\nWrite CSV/JSON outputs, model files and figures for repeatable review.',650,225,542,420,21);
notes(slides[8],'The seven detector inputs are eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and derived isRoot. Unknown categorical values map to -1. The main export has month-level time, limiting event-sequence analysis.', ['src/features/event_features.py','configs/model.yaml']);

box(slides[9],'Inputs: API name, AWS service, region, identity type, error code, instance type and root flag.\nTraining-only maps. Unseen categories use −1. The source stays read-only.',88,155,1104,75,18);
table(slides[9],[
  ['Module','Main task','Saved output'],
  ['Data preparation','Audit source, encode inputs\nand build monthly windows','Manifest and features'],
  ['Detector and SHAP','Fit Isolation Forest and verify\nSHAP additivity','Model, scores and SHAP'],
  ['Drift diagnosis','Measure PSI, SHAP drift\nand feature coupling','Signals and drift states'],
  ['Protected update','Use replay and normal candidates\nwhen the policy requests a refit','Candidates and model'],
  ['Evaluation','Compare policies on identical\nscenario and seed pairs','Metrics and paired tests'],
],{y:230,height:315,widths:[285,495,324],pt:18,padding:3});
box(slides[9],'SHAP additivity residual: 2.66e-14. Reports read saved experiment results.',88,625,1104,28,18);
notes(slides[9],'The seven exact model inputs are eventName, eventSource, awsRegion, userIdentitytype, errorCode, requestParametersinstanceType and derived isRoot. Fit maps on training rows only and map unseen categories to -1. Requirements: keep source data unchanged, preserve time order, separate evaluation labels, save scores and SHAP values, log update decisions and produce auditable CSV/JSON evidence. Implementation modules: src/features/event_features.py; src/explain/shap_explainer.py; src/drift/drift_monitor.py; src/drift/diagnosis.py; src/adaptation/controller.py; src/evaluation/metrics.py. The merged slide retains functional requirements and implementation coverage within the 15-slide limit.', ['src','README.md']);

box(slides[10],'7 scenarios: stable, 3 routine changes and 3 security-related changes.\nMain change intensity: 25%. 5 validation seeds, 10 test seeds and 70 test units per rule.\nValidation diagnosis macro-F1: 0.7306.',88,155,1104,95,19);
table(slides[10],[
  ['Update rule','Mean F1','False-positive rate','Unnecessary updates'],
  ['No update','0.2901','0.4282','0.0000'],
  ['Periodic','0.2888','0.3160','0.2000'],
  ['Data change only','0.2734','0.1825','0.3286'],
  ['SHAP change only','0.2873','0.3397','0.0000'],
  ['Dual signals','0.2873','0.3397','0.0000'],
  ['Coupling','0.2873','0.3397','0.0000'],
],{y:245,height:270,widths:[340,190,280,294],pt:18});
box(slides[10],'Dual false-positive rate fell from 0.4282 to 0.3397, an 8.85 percentage-point drop.\nThe F1 difference was inconclusive. Coupling and SHAP-only matched the dual rule.\nDual and coupling avoided unnecessary updates in these controlled tests.',88,565,1104,90,18);
notes(slides[10],'Controlled benchmark only: 7 scenario families times 10 held-out seeds gives 70 paired scenario-seed units per policy. Five separate validation seeds tune thresholds. Dual validation diagnosis macro-F1 is 0.7306. The paired dual-minus-static FPR difference is -0.088478, 95% CI [-0.127232,-0.056106], BH q=0.000434. Paired F1 difference is -0.002796 with CI [-0.018096,0.011245]. The interval crosses zero. Unnecessary update rate uses all evaluated runs as denominator. Coupling and SHAP-only match dual under current settings, including the conservative-coupling ablation. These are not attack metrics on the primary unlabelled corpus.', ['results/adaptation_summary.csv','results/paired_inference.csv','data/benchmark/diagnosis_thresholds.json']);

box(slides[11],'Independent corpus [13]: 16,495 training events and 24,087 test events.\nTest labels: 2,585 attack events and 21,502 benign events.\nIsolation Forest: precision 0.3306, recall 0.7137, F1 0.4519 and FPR 0.1738.',88,160,1104,105,20);
box(slides[11],'Drift checkpoint: 12 windows (10 security and 2 benign)',88,285,1104,45,22,{bold:true});
table(slides[11],[
  ['Rule','Recall','F1','False-positive rate'],
  ['Dual signals','1.0000','0.9524','0.5000'],
  ['Coupling: source threshold','0.1000','0.1818','0.0000'],
  ['Coupling: target threshold','1.0000','1.0000','0.0000'],
],{y:345,height:200,widths:[510,160,160,274],pt:18});
box(slides[11],'The source coupling threshold missed 9 of the 10 security windows.\nTarget calibration separated all 12 windows using only unlabelled scores.\nIt used the current target batch. Later unseen windows still need testing.',88,565,1104,90,20);
notes(slides[11],'Keep the two evaluation units separate. Detector-only evaluation uses 16,495 benign training and 24,087 mixed test records (2,585 attack-labelled, 21,502 benign). The temporal checkpoint uses 12 scenario windows, including 10 security and 2 benign windows. Feature-only, SHAP-only and dual match. Source coupling transferred poorly. Unsupervised largest-gap calibration selects 0.4990795305 from target conservative scores after source-locked feature/SHAP gates. It uses the evaluated target batch, so this is exploratory transductive calibration, not prospective validation or full post-adaptation recovery.', ['data/external_validation/external_validation_manifest.json','data/external_validation/external_detector_metrics.csv','data/external_validation/external_temporal_diagnosis_metrics.json','docs/unsupervised_transfer_calibration.md']);

box(slides[12],'What the project shows',88,170,510,40,23,{bold:true});
box(slides[12],'A local pipeline connects data checks, SHAP explanations and model updates.\n\nDual signals lowered false alarms in controlled tests.\n\nCoupling makes feature alignment explicit, but did not improve current policy results.\n\nAll 28 automated software tests pass.',88,230,510,350,20);
box(slides[12],'Limits and next steps',665,170,527,40,23,{bold:true});
box(slides[12],'The primary corpus has no attack labels.\n\nMonthly timestamps limit detailed session analysis.\n\nTest longer streams with more independent incidents.\n\nImprove scenario consistency and compare matched model settings.',665,230,527,350,20);
box(slides[12],'Cost sensitivity: no update rule was best for every assumed cost setting.',88,620,1104,30,19);
notes(slides[12],'Do not claim coupling superiority or general reliability from the current results. The primary corpus has no attack labels. Controlled perturbations and target-batch calibration have specific limitations. Future work includes consistent derived features, matched-size refits and independent temporal recovery.', ['LIMITATIONS.md','docs/next_experiments.md']);

table(slides[13],[
  ['Deliverable','Evidence available'],
  ['Working prototype','Python modules, trained baseline and saved scores'],
  ['Experimental results','Monthly signals, policy comparisons and external checks'],
  ['Quality checks','28 tests pass and SHAP additivity is verified'],
  ['Documentation','Capstone report and research draft; no publication claim'],
],{y:170,height:285,widths:[330,774],pt:19});
box(slides[13],'Live demonstration',88,480,1104,38,23,{bold:true});
box(slides[13],'1. Check the dataset manifest and monthly split.\n2. Show drift, coupling and the model-update decisions.\n3. Compare saved results and run the automated tests.',88,530,1104,90,21);
box(slides[13],'github.com/sani3055/DriftDetection',88,632,1104,25,18);
notes(slides[13],'Demonstration path: manifest and temporal split; model feature contract; score and SHAP samples; monthly drift and coupling CSVs; controlled diagnosis and adaptation rows; independent transfer metrics. Commands: python scripts/run_all.py; python scripts/run_external_temporal_diagnosis.py; python -m pytest tests -q. The saved validation record reports 28 passing tests. The source CSV is external and required for full regeneration. A 100-record literature collection is not a finished PRISMA review. Publication, patent, outcome-form submission and supervisor approval are not established by this presentation.', ['docs/final_validation.md','README.md','outputs/BCSE497J_Capstone_Report_Submission_Ready.docx']);

const referenceLines=[
  '[1] Kuppa and Le-Khac. Learn to Adapt. C&EE, 2022.',
  '[2] Han et al. Normality Shift Detection, Explanation and Adaptation. NDSS, 2023.',
  '[3] Lee et al. Explainable Model Drift Detection in Unsupervised Environments. CMC, 2023.',
  '[4] Li et al. Concept Drift Adaptation by Exploiting Drift Type. ACM TKDD, 2024.',
  '[5] Arora, Rani and Saxena. Review of Concept Drift Detection and Adaptation. WIREs DMKD, 2024.',
  '[6] Decker et al. Explanatory Model Monitoring. ACM KDD, 2024.',
  '[7] Varma.I and Ramya K. Explainable ML and LLM Framework for CloudTrail Logs. ICNGN, 2025.',
  '[8] Maseno, Sun and Wang. Detecting Adversarial Evasion Using Explainable AI. IJIS, 2026.',
  '[9] Liu, Ting and Zhou. Isolation Forest. IEEE ICDM, 2008.',
  '[10] Lundberg and Lee. A Unified Approach to Interpreting Model Predictions. NeurIPS, 2017.',
  '[11] AWS. Understanding CloudTrail Events. CloudTrail documentation.',
  '[12] AWS. Feature Attribution Drift for Models in Production. SageMaker documentation.',
  '[13] ArielCyber. Cloud Log Sampling. Public dataset repository.',
];
for(let i=0;i<referenceLines.length;i++){
  const col=i<7?0:1;const row=col===0?i:i-7;
  box(slides[14],referenceLines[i],88+col*570,172+row*67,534,63,18);
}
notes(slides[14],'Titles on the slide are shortened for readability. Full titles, author metadata and primary verification links for [1]–[8] are in docs/review3_literature_evidence.md and the literature-slide notes. [1] https://doi.org/10.1016/j.compeleceng.2022.108239 [2] https://doi.org/10.14722/ndss.2023.24830 [3] https://doi.org/10.32604/cmc.2023.040235 [4] https://doi.org/10.1145/3638777 [5] https://doi.org/10.1002/widm.1536 [6] https://doi.org/10.1145/3637528.3671959 [7] https://doi.org/10.1109/ICNGN67480.2025.11413642 [8] https://doi.org/10.1007/s10207-026-01299-x [9] https://doi.org/10.1109/ICDM.2008.17 [10] https://proceedings.neurips.cc/paper_files/paper/2017/hash/8a20a8621978632d76c43dfd28b67767-Abstract.html [11] https://docs.aws.amazon.com/awscloudtrail/latest/userguide/cloudtrail-events.html [12] https://docs.aws.amazon.com/sagemaker/latest/dg/clarify-model-monitor-feature-attribution-drift.html [13] https://github.com/ArielCyber/cloud_log_sampling. References in this standalone deck use their own numbering, separate from the report.', ['docs/literature_matrix.csv','docs/review3_literature_evidence.md']);

const speakingPoints={
  2:'Explain that the project keeps the same historical corpus but now asks when the detector should be updated. The approval slide is a required administrative section, and an authentic guide email is still needed.',
  3:'A new region or service can be normal. Updating after every change can waste work or learn unwanted behaviour. The aim is to compare what changed in the data with what changed in the model’s explanations before refitting.',
  4:'Use two evidence tracks: describe real monthly changes without claiming attack accuracy, then use controlled changes with known masks to measure decisions. The independent labelled dataset supplies a separate validation check.',
  6:'For each of five shared fields, calculate a data-change score and an attribution-change score. Cosine similarity measures how well these two patterns line up. Low change, benign drift, model-relevant drift and disagreement lead to different decisions. The score is a proposal to evaluate, not proof of malicious intent.',
  7:'Define unnecessary update as a requested update in a stable or routine-change scenario, divided by all evaluated scenario runs. Report it alongside F1 and false positives rather than using it as the only success measure.',
  8:'Isolation Forest learns unusual feature combinations. Contamination 0.05 sets its outlier cutoff and does not mean that five percent of the real data is attacked. The safeguard admits only baseline-normal current rows and keeps replay data. This reduces exposure but cannot guarantee zero contamination.',
  9:'The seven model inputs are a subset of the eighteen original columns. Direct account IDs and access-key strings are not model inputs. The mapping is fixed after training so later categories do not alter the learned vocabulary.',
  10:'PSI measures how category proportions changed. SHAP drift measures how the explanation distribution changed. The additivity check reconstructs the explained model output, which checks numerical consistency and does not prove the detector is correct about security.',
  11:'Read the whole table. Data-only updates achieve a lower false-positive rate but trigger many unnecessary changes and have lower mean F1. Dual and coupling have the same current outcome. Explain the 8.85 percentage-point FPR reduction relative to the static baseline and retain the inconclusive F1 finding.',
  12:'Separate event-level detector metrics from scenario-window diagnosis metrics. A threshold that worked on the source transferred poorly. The largest-gap threshold uses the current target scores without attack labels, so its perfect twelve-window result still needs prospective validation.',
  13:'The capstone delivers a working integrated prototype and a tested research question. Stronger research needs realistic changes, consistent features, independent time periods and a persistent sequence of updates. No policy wins every assumed cost trade-off.',
  14:'Open the manifest, temporal split and one monthly drift row. Follow that row’s feature and SHAP evidence to the diagnosis, then show a controlled policy result with its candidate count. Finish by running python -m pytest tests -q and opening the external validation summary.',
};
for(const [slideNumber,explanation] of Object.entries(speakingPoints)){
  const slide=slides[Number(slideNumber)-1];
  slide.speakerNotes.text+='\n\nPresentation explanation\n'+explanation;
}

// A second literature slide replaces the separate inputs slide. All inputs and
// functional requirements now appear on the combined implementation slide.
const beforeLiterature=[...deck.slides.items];
const literatureB=deck.slides.add({layoutId:layout?.id ?? 'p83mt83u'});
box(literatureB,'Literature Survey 2: Explanations and Cloud Logs',88,71.5,1104,65,30,{bold:true});
table(literatureB,[
  ['Paper','Objective','Method','Limit / scope','Project response'],
  ['[5] Arora et al.\n2024','Review drift\nresearch','Survey detection\nand adaptation','Broad review.\nNo cloud experiment.','Frame our\nresearch gaps.'],
  ['[6] Decker et al.\n2024','Explain effects\nof feature shift','Optimal transport\nand Shapley values','General monitoring.\nDifferent update task.','Test alignment\nbefore updating.'],
  ['[7] Varma &\nRamya, 2025','Explain cloud\nanomalies','ML detection and\nLLM explanations','Simulated events.\nDifferent policy.','Measure unnecessary\nmodel updates.'],
  ['[8] Maseno et al.\n2026','Detect evasion\nin network IDS','SHAP displacement\nand top-k overlap','Supervised IDS.\nDifferent data.','Test unlabelled\nCloudTrail drift.'],
],{y:170,height:355,widths:[195,190,245,250,224],pt:18});
box(literatureB,'Eight selected studies from 2022–2026: five journal papers and three conference papers.\nThese comparisons motivate our design. We do not claim to outperform these methods.',88,590,1104,65,18);
box(literatureB,'28-10-2026',88,667.33,288,38.33,12,{color:'#8B8B8B'});
box(literatureB,'SCOPE',424,667.33,432,38.33,12,{color:'#8B8B8B',alignment:'center'});
box(literatureB,'6',904,667.33,288,38.33,12,{color:'#8B8B8B',alignment:'right'});
notes(literatureB,'[5] Shruti Arora, Rinkle Rani and Nitin Saxena, A Systematic Review on Detection and Adaptation of Concept Drift in Streaming Data Using Machine Learning Techniques, WIREs Data Mining and Knowledge Discovery 14(4), e1536 (2024). https://wires.onlinelibrary.wiley.com/doi/10.1002/widm.1536 [6] Thomas Decker, Alexander Koebler, Michael Lebacher, Ingo Thon, Volker Tresp and Florian Buettner, Explanatory Model Monitoring to Understand the Effects of Feature Shifts on Performance, KDD 2024, pp. 550–561. https://arxiv.org/abs/2408.13648 and https://doi.org/10.1145/3637528.3671959 XPE combines optimal transport with Shapley values to explain estimated performance changes. [7] Surya Karthikeya Varma.I and Ramya K, An Explainable Machine Learning and Large Language Model Framework for Anomaly Detection in AWS CloudTrail Logs, ICNGN 2025, pp. 1–5. https://doi.org/10.1109/ICNGN67480.2025.11413642 Author metadata verified through the publisher-deposited Crossref record. [8] E. M. Maseno, Y. Sun and Z. Wang, Detecting Adversarial Evasion in Deep Learning Intrusion Detection Systems Using Explainable AI, International Journal of Information Security 25, 125 (2026), published 15 July 2026. https://link.springer.com/article/10.1007/s10207-026-01299-x That work measures SHAP explanation displacement and dominant-feature stability in recurrent network IDS models. It differs from our unlabelled CloudTrail diagnosis and adaptation task. No head-to-head reproduction is claimed. Explain that the specific contribution is the tested CloudTrail protocol and coupling question, with neutral and negative results retained.', ['docs/literature_matrix.csv','docs/review3_literature_evidence.md']);
deck.delete('sl/'+beforeLiterature[8].id);
deck.slides.reorder([...beforeLiterature.slice(0,5),literatureB,...beforeLiterature.slice(5,8),...beforeLiterature.slice(9)].map(s=>'sl/'+s.id));
for(const [i,slide] of deck.slides.items.entries()){
  for(const shape of slide.shapes.items){
    if(shape.position.top>660 && shape.position.left>850)shape.text=String(i+1);
  }
}

await (await PresentationFile.exportPptx(deck)).save(path.join(tmp,'candidate.pptx'));
await fs.writeFile(path.join(tmp,'authored-inspection.ndjson'),(await deck.inspect({kind:'slide,textbox,table',maxChars:80000})).ndjson);
const {finalizePresentation}=await import(pathToFileURL(path.join(skill,'container_tools/artifact_tool_utils.mjs')).href);
const final=path.join(root,'outputs/Review_3_Capstone_Final.pptx');
const result=await finalizePresentation({
  workspaceDir:root,candidatePath:path.join(tmp,'candidate.pptx'),finalPath:final,
  pythonExecutable:path.join(dependencies,'python/python.exe'),
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  explicitTotalSlideCount:15,requiredNativeTableOwnerSlides:[5,6,7,10,11,12,14],
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit',...[5,6,7,10,11,12,14].flatMap(n=>['--require-native-table-slide',String(n)])],
  fontPolicy:{basis:'reference',families:['Times New Roman','Calibri'],referencePath:source,referenceSha256:createHash('sha256').update(await fs.readFile(source)).digest('hex')},
  verifyArtifactToolImport:true,receiptPath:path.join(tmp,`validation-${Date.now()}.json`),
});
console.log(JSON.stringify(result));
