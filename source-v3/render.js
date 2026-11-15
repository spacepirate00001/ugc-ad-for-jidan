const {chromium}=require('playwright');const {spawn}=require('child_process');const fs=require('fs');
const dir=process.argv[2], mode=process.argv[3];
(async()=>{
 const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
 await p.goto('file://'+dir+'/ad.html');await p.evaluate(()=>document.fonts.ready);
 await p.waitForLoadState('networkidle');await p.waitForTimeout(500);
 const total=await p.evaluate(()=>TOTAL);
 fs.writeFileSync(dir+'/scenes.json',JSON.stringify(await p.evaluate(()=>({total:TOTAL,starts:SCENES}))));
 if(mode==='stills'){for(const t of process.argv.slice(4)){await p.evaluate(t=>render(t),+t);await p.screenshot({path:`${dir}/still_${t}.jpg`,quality:80,type:'jpeg'});}await b.close();return;}
 const fps=30,N=Math.round(total*fps);
 const ff=spawn('ffmpeg',['-y','-loglevel','error','-f','image2pipe','-framerate',''+fps,'-c:v','mjpeg','-i','-','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',dir+'/video_noaudio.mp4']);
 ff.stderr.pipe(process.stderr);
 for(let i=0;i<N;i++){await p.evaluate(t=>render(t),i/fps);const buf=await p.screenshot({type:'jpeg',quality:92});
   if(!ff.stdin.write(buf)) await new Promise(r=>ff.stdin.once('drain',r)); if(i%150==0)console.log(i,'/',N);}
 ff.stdin.end();await new Promise(r=>ff.on('close',r));await b.close();
})();
