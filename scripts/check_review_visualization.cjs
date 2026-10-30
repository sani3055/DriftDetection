const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');
const {chromium}=require('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

(async()=>{
 const out=path.resolve(__dirname,'../tmp/review_visualization');
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try {
  const page=await browser.newPage({viewport:{width:850,height:1000}});
  const errors=[];
  page.on('pageerror',e=>errors.push(e.message));
  const preview=execFileSync('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/python.exe',[
   '-X','utf8','C:/Users/Lenovo/.codex/plugins/cache/openai-bundled/visualize/1.0.55/skills/visualize/scripts/render.py',
   'C:/Users/Lenovo/.codex/visualizations/2026/10/21/01a15f1a-3291-7bc1-bdf4-246c4a8b3ae9/cloudtrail-review-demo.html'
  ],{encoding:'utf8',maxBuffer:2000000});
  await page.setContent(preview);
  const frame=page.frameLocator('iframe');
  await frame.locator('#cloudtrail-example').waitFor();
  const expected={stable:['stable','false','true'],benign_region:['benign_drift','false','true'],benign_identity:['benign_drift','false','true'],benign_service:['benign_drift','false','true'],security_privilege:['benign_drift','false','false'],security_defense:['security_relevant_drift','true','true'],security_credential:['security_relevant_drift','true','true']};
  for(const [scenario,values] of Object.entries(expected)){
   await frame.locator('#cloudtrail-example').selectOption(scenario);
   const actual=await frame.locator('#cloudtrail-review-demo').evaluate(root=>[root.dataset.diagnosis,root.dataset.update,root.dataset.matches]);
   if(JSON.stringify(values)!==JSON.stringify(actual))throw new Error(`${scenario}: ${actual}`);
  }
  await frame.locator('#cloudtrail-example').selectOption('security_defense');
  await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
  await page.setViewportSize({width:360,height:1000});
  await frame.locator('#cloudtrail-example').selectOption('security_privilege');
  await page.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
  const overflow=await frame.locator('#cloudtrail-review-demo').evaluate(root=>{
   const bounds=root.getBoundingClientRect();
   return [...root.querySelectorAll('svg text')].filter(el=>{
    const r=el.getBoundingClientRect();return r.left<bounds.left-1||r.right>bounds.right+1;
   }).map(el=>el.textContent);
  });
  if(overflow.length)throw new Error('Chart labels overflow: '+overflow.join(', '));
  if(errors.length)throw new Error(errors.join('\n'));
  console.log(JSON.stringify({testedScenarios:7,desktopScreenshot:path.join(out,'desktop.png'),mobileScreenshot:path.join(out,'mobile.png'),pageErrors:errors,overflow}));
 } finally {await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
