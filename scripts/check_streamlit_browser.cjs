const fs=require('node:fs');
const path=require('node:path');
const {chromium}=require('C:/Users/Lenovo/.cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules/playwright');

(async()=>{
 const out=path.resolve(__dirname,'../tmp/streamlit_demo');
 fs.mkdirSync(out,{recursive:true});
 const browser=await chromium.launch({headless:true,executablePath:'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe'});
 try {
  const page=await browser.newPage({viewport:{width:1250,height:1100}});
  const errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:8501/');
  await page.getByRole('heading',{name:'CloudTrail Drift Diagnosis',exact:true}).waitFor({timeout:60000});
  await page.getByRole('heading',{name:'Stable period',exact:true}).waitFor({timeout:60000});
  await page.locator('[data-testid="stVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg').first().waitFor({timeout:30000});
  if(await page.getByText('Traceback').count())throw new Error('App traceback displayed');
  const scenario=page.getByRole('combobox',{name:'Test scenario',exact:true});
  await scenario.click();
  await page.getByRole('option',{name:'Routine change: AWS region',exact:true}).click();
  await page.getByRole('heading',{name:'Routine drift',exact:true}).waitFor();
  await scenario.click();
  await page.getByRole('option',{name:'Simulated security change: defence',exact:true}).click();
  await page.getByRole('heading',{name:'Security-relevant drift',exact:true}).waitFor();
  await page.screenshot({path:path.join(out,'desktop.png'),fullPage:true});
  await scenario.click();
  await page.getByRole('option',{name:'Simulated security change: privilege',exact:true}).click();
  await page.getByText('Missed security-related scenario:',{exact:false}).waitFor();
  await page.screenshot({path:path.join(out,'missed-case.png'),fullPage:true});
  const mobile=await browser.newPage({viewport:{width:390,height:1000}});
  await mobile.goto('http://127.0.0.1:8501/');
  await mobile.getByRole('heading',{name:'Stable period',exact:true}).waitFor({timeout:60000});
  await mobile.locator('[data-testid="stVegaLiteChart"] canvas, [data-testid="stVegaLiteChart"] svg').first().waitFor({timeout:30000});
  await mobile.screenshot({path:path.join(out,'mobile.png'),fullPage:true});
  const overflow=await mobile.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth+2);
  if(overflow)throw new Error('Horizontal overflow at mobile width');
  if(errors.length)throw new Error(errors.join('\n'));
  console.log(JSON.stringify({desktopScreenshot:path.join(out,'desktop.png'),missedCaseScreenshot:path.join(out,'missed-case.png'),mobileScreenshot:path.join(out,'mobile.png'),pageErrors:errors,mobileOverflow:overflow}));
 }finally{await browser.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
