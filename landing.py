"""MediLens landing hero: 3D DNA helix + particles + faint grid, rendered in an iframe."""

HTML = r"""
<!DOCTYPE html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@700;800&family=DM+Sans:wght@400;500&display=swap" rel="stylesheet">
<style>
  html,body{margin:0;height:100%;background:transparent;overflow:hidden;font-family:'DM Sans',sans-serif;color:#F4F8FC}
  canvas{position:absolute;inset:0}
  .grid{position:absolute;inset:0;opacity:.10;
    background-image:linear-gradient(#36C5F0 1px,transparent 1px),linear-gradient(90deg,#36C5F0 1px,transparent 1px);
    background-size:46px 46px; mask-image:radial-gradient(circle at 50% 40%,#000 10%,transparent 70%);}
  .stage{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;
         text-align:center;perspective:900px;padding:0 24px;pointer-events:none}
  h1{margin:0;font-family:'Sora',sans-serif;font-weight:800;font-size:clamp(40px,7.5vw,92px);line-height:1.02;
     transform-style:preserve-3d;transition:transform .15s ease-out;letter-spacing:-.01em}
  .ch{display:inline-block;opacity:0;transform:rotateX(-100deg) translateZ(-120px);transform-origin:50% 100%;
      animation:in .9s cubic-bezier(.2,.9,.2,1) forwards;
      text-shadow:0 0 30px rgba(54,197,240,.45),0 0 70px rgba(66,230,181,.25)}
  @keyframes in{to{opacity:1;transform:rotateX(0) translateZ(0)}}
  .sub{margin-top:22px;max-width:560px;font-weight:600;font-size:clamp(16px,1.7vw,20px);color:#7FB3FF;
       opacity:0;animation:fade .8s 1.6s forwards}
  .support{margin-top:10px;max-width:520px;font-size:clamp(13px,1.3vw,15px);line-height:1.5;color:#AFC1D1;
       opacity:0;animation:fade .8s 1.9s forwards}
  @keyframes fade{to{opacity:1}}
  @media (prefers-reduced-motion:reduce){.ch{animation-duration:.01s}.sub,.support{animation-duration:.01s;animation-delay:0s}}
</style></head><body>
<div class="grid"></div>
<div class="stage"><h1 id="title"></h1><p class="sub">__TAGLINE__</p><p class="support">__SUPPORT__</p></div>
<script src="https://cdnjs.cloudflare.com/ajax/libs/three.js/r128/three.min.js"></script>
<script>
const title=document.getElementById('title');let n=0;
"__NAME__".split(' ').forEach(w=>{
  const el=document.createElement('span');el.style.display='block';
  [...w].forEach(c=>{const s=document.createElement('span');s.className='ch';s.textContent=c;
    s.style.animationDelay=(n++*0.05)+'s';el.appendChild(s)});
  title.appendChild(el)});
window.addEventListener('mousemove',e=>{
  const x=(e.clientX/innerWidth-.5),y=(e.clientY/innerHeight-.5);
  title.style.transform=`rotateY(${x*12}deg) rotateX(${-y*8}deg)`});

const scene=new THREE.Scene();
const cam=new THREE.PerspectiveCamera(50,innerWidth/innerHeight,.1,100);cam.position.set(0,0,15);
const r=new THREE.WebGLRenderer({antialias:true,alpha:true});
r.setPixelRatio(Math.min(devicePixelRatio,2));r.setSize(innerWidth,innerHeight);
document.body.prepend(r.domElement);
const helix=new THREE.Group();scene.add(helix);
const A=new THREE.MeshBasicMaterial({color:0x36C5F0}),B=new THREE.MeshBasicMaterial({color:0x42E6B5});
const sg=new THREE.SphereGeometry(.15,16,16),lm=new THREE.LineBasicMaterial({color:0x1E4A63,transparent:true,opacity:.6});
const N=46,H=22,R=2.6,T=5.5;
for(let i=0;i<N;i++){
  const t=i/N,a=t*Math.PI*2*T,y=(t-.5)*H;
  const p1=new THREE.Vector3(Math.cos(a)*R,y,Math.sin(a)*R),p2=new THREE.Vector3(-Math.cos(a)*R,y,-Math.sin(a)*R);
  const s1=new THREE.Mesh(sg,A),s2=new THREE.Mesh(sg,B);s1.position.copy(p1);s2.position.copy(p2);
  helix.add(s1,s2,new THREE.Line(new THREE.BufferGeometry().setFromPoints([p1,p2]),lm));}
helix.rotation.z=.3;
const pg=new THREE.BufferGeometry(),pn=220,pos=new Float32Array(pn*3);
for(let i=0;i<pn*3;i++)pos[i]=(Math.random()-.5)*40;
pg.setAttribute('position',new THREE.BufferAttribute(pos,3));
const pts=new THREE.Points(pg,new THREE.PointsMaterial({color:0x7FE7DA,size:.05,transparent:true,opacity:.5}));scene.add(pts);
const still=matchMedia('(prefers-reduced-motion:reduce)').matches;
(function loop(){requestAnimationFrame(loop);
  if(!still){helix.rotation.y+=.0035;pts.rotation.y-=.0006;}
  r.render(scene,cam)})();
addEventListener('resize',()=>{cam.aspect=innerWidth/innerHeight;cam.updateProjectionMatrix();r.setSize(innerWidth,innerHeight)});
</script></body></html>
"""


def landing_html(name: str, tagline: str, support: str) -> str:
    return HTML.replace("__NAME__", name).replace("__TAGLINE__", tagline).replace("__SUPPORT__", support)
