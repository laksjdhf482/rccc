
import streamlit as st
import streamlit.components.v1 as components

st.set_page_config(
    page_title="RPG 운전·주차 게임",
    page_icon="🚗",
    layout="wide",
    initial_sidebar_state="collapsed",
)

HTML = r"""
<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
*{box-sizing:border-box}
html,body{margin:0;background:#111;color:#fff;font-family:Arial,"Noto Sans KR",sans-serif}
body{overflow:hidden}
#game{width:100vw;height:100vh;display:flex;flex-direction:column;background:#151515}
#top{height:58px;display:flex;align-items:center;gap:10px;padding:8px 12px;background:#202020;border-bottom:1px solid #444;flex-wrap:wrap}
button,select{background:#2d2d2d;color:#fff;border:1px solid #666;border-radius:7px;padding:8px 12px;font-size:14px;cursor:pointer}
button:hover{background:#3a3a3a}
#money{margin-left:auto;font-weight:700;color:#ffd84d}
#stage{font-weight:700}
#wrap{flex:1;position:relative;min-height:0}
canvas{display:block;width:100%;height:100%;background:#5d8b4b}
#hud{position:absolute;left:12px;top:12px;background:rgba(0,0,0,.68);padding:10px 12px;border-radius:9px;line-height:1.55;min-width:180px;font-size:13px}
#result{position:absolute;right:12px;top:12px;width:250px;background:rgba(0,0,0,.78);padding:14px;border-radius:10px;display:none}
#result h3{margin:0 0 10px}
#result div{margin:5px 0}
#help{position:absolute;left:50%;bottom:12px;transform:translateX(-50%);background:rgba(0,0,0,.65);padding:8px 14px;border-radius:999px;font-size:12px;white-space:nowrap}
#garage{position:absolute;inset:0;background:rgba(0,0,0,.9);display:none;overflow:auto;padding:24px}
#garage h2{margin-top:0}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px;max-width:900px}
.carcard{background:#252525;border:1px solid #555;border-radius:10px;padding:14px}
.swatch{height:65px;border-radius:8px;margin-bottom:10px;border:2px solid #888}
.lock{opacity:.55}
.small{font-size:12px;color:#bbb}
#message{position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);background:rgba(0,0,0,.82);padding:18px 24px;border-radius:12px;text-align:center;display:none;z-index:4}
@media(max-width:700px){
 #top{height:90px}
 #money{margin-left:0}
 #help{display:none}
}
</style>
</head>
<body>
<div id="game">
  <div id="top">
    <select id="mode">
      <option value="free">자유주행</option>
      <option value="test">운전면허시험</option>
      <option value="parking">주차</option>
    </select>
    <select id="car"></select>
    <button id="start">새 미션</button>
    <button id="garageBtn">차량 구매</button>
    <span id="stage">STAGE 1</span>
    <span id="money">보유금액 0원</span>
  </div>
  <div id="wrap">
    <canvas id="canvas"></canvas>
    <div id="hud"></div>
    <div id="result">
      <h3>운전 결과</h3>
      <div id="rText"></div>
      <button id="again">다시 도전</button>
    </div>
    <div id="help">↑ 전진 · ↓ 후진 · ← → 조향 · SPACE 시점 전환</div>
    <div id="message"></div>
    <div id="garage">
      <button id="closeGarage">닫기</button>
      <h2>차량 구매</h2>
      <p class="small">운전·주차로 돈을 벌어 새로운 자동차를 구매하세요</p>
      <div id="cars" class="grid"></div>
    </div>
  </div>
</div>

<script>
const canvas=document.getElementById("canvas"), ctx=canvas.getContext("2d");
const modeEl=document.getElementById("mode"), carEl=document.getElementById("car");
const hud=document.getElementById("hud"), moneyEl=document.getElementById("money");
const stageEl=document.getElementById("stage"), result=document.getElementById("result");
const rText=document.getElementById("rText"), message=document.getElementById("message");
const garage=document.getElementById("garage"), carsEl=document.getElementById("cars");

const cars=[
 {id:"morning",name:"모닝",price:0,w:28,l:48,color:"#e84d4d",turn:.050},
 {id:"sedan",name:"승용차",price:50000,w:31,l:53,color:"#3d86e8",turn:.047},
 {id:"suv",name:"SUV",price:180000,w:36,l:60,color:"#28a66a",turn:.043},
 {id:"truck1",name:"1톤 트럭",price:350000,w:40,l:72,color:"#f0a62b",turn:.038},
 {id:"truck2",name:"대형 트럭",price:800000,w:46,l:92,color:"#a86de8",turn:.032},
 {id:"bmw",name:"BMW",price:1500000,w:34,l:58,color:"#222",turn:.046},
 {id:"escalade",name:"캐딜락 에스컬레이드",price:3000000,w:40,l:72,color:"#d7d7d7",turn:.040},
 {id:"sport",name:"스포츠카",price:5000000,w:32,l:56,color:"#ef315c",turn:.052}
];
let owned=new Set(["morning"]);
let money=0, stage=1, view=3, running=false, startTime=0, elapsed=0, earned=0;
let keys={}, last=performance.now(), mission=null;
let player={x:0,y:0,a:0,s:0};
let parkingTarget={x:0,y:0,a:0,w:80,l:125};
let obstacles=[], traffic=[];
let selectedCar=cars[0];

function resize(){
 canvas.width=canvas.clientWidth*devicePixelRatio;
 canvas.height=canvas.clientHeight*devicePixelRatio;
 ctx.setTransform(devicePixelRatio,0,0,devicePixelRatio,0,0);
}
window.addEventListener("resize",resize); resize();

function moneyText(n){return Math.floor(n).toLocaleString("ko-KR")+"원"}
function carById(id){return cars.find(c=>c.id===id)}
function refreshCars(){
 carEl.innerHTML="";
 cars.forEach(c=>{
  const o=document.createElement("option");o.value=c.id;
  o.textContent=owned.has(c.id)?c.name:c.name+" 🔒";
  carEl.appendChild(o);
 });
 if(!owned.has(carEl.value))carEl.value="morning";
 selectedCar=carById(carEl.value);
}
function refreshMoney(){
 moneyEl.textContent="보유금액 "+moneyText(money);
 stageEl.textContent="STAGE "+stage;
}
function showMsg(t){
 message.innerHTML=t; message.style.display="block";
 setTimeout(()=>message.style.display="none",1200);
}

function drawCar(x,y,a,c,playerCar=false){
 ctx.save();ctx.translate(x,y);ctx.rotate(a);
 ctx.fillStyle=playerCar?c.color:"#f5f5f5";
 ctx.strokeStyle=playerCar?"#111":"#999";ctx.lineWidth=2;
 ctx.fillRect(-c.w/2,-c.l/2,c.w,c.l);ctx.strokeRect(-c.w/2,-c.l/2,c.w,c.l);
 ctx.fillStyle="#222";ctx.fillRect(-c.w*.38,-c.l*.22,c.w*.76,c.l*.23);
 ctx.fillStyle="#222";ctx.fillRect(-c.w*.38,c.l*.05,c.w*.76,c.l*.23);
 ctx.fillStyle="#ddd";ctx.fillRect(-c.w*.36,-c.l*.43,c.w*.72,5);
 ctx.fillStyle="#d44";ctx.fillRect(-c.w*.35,c.l*.36,c.w*.7,5);
 ctx.restore();
}

function road(){
 const W=canvas.clientWidth,H=canvas.clientHeight;
 ctx.fillStyle="#60904e";ctx.fillRect(0,0,W,H);
 ctx.fillStyle="#464646";
 ctx.fillRect(W*.20,0,W*.60,H);
 ctx.strokeStyle="#e8e8e8";ctx.lineWidth=4;
 ctx.setLineDash([28,24]);
 ctx.beginPath();ctx.moveTo(W*.50,0);ctx.lineTo(W*.50,H);ctx.stroke();ctx.setLineDash([]);
 ctx.strokeStyle="#fff";ctx.lineWidth=8;
 ctx.beginPath();ctx.moveTo(W*.20,0);ctx.lineTo(W*.20,H);ctx.moveTo(W*.80,0);ctx.lineTo(W*.80,H);ctx.stroke();
 for(let y=-20;y<H;y+=70){
  ctx.fillStyle="#777";ctx.fillRect(W*.05,y,Math.max(35,W*.10),38);
  ctx.fillStyle="#777";ctx.fillRect(W*.85,y,Math.max(35,W*.10),38);
 }
}

function worldToScreen(wx,wy){
 const W=canvas.clientWidth,H=canvas.clientHeight;
 if(view===3){
  return {x:W/2+(wx-player.x),y:H/2+(wy-player.y)};
 }
 return {x:W/2+(wx-player.x),y:H*.72+(wy-player.y)*.42};
}

function drawWorld(){
 road();
 const W=canvas.clientWidth,H=canvas.clientHeight;
 // parking target
 let p=worldToScreen(parkingTarget.x,parkingTarget.y);
 ctx.save();ctx.translate(p.x,p.y);ctx.rotate(parkingTarget.a);
 ctx.strokeStyle="#ffd84d";ctx.lineWidth=3;ctx.setLineDash([8,7]);
 ctx.strokeRect(-parkingTarget.w/2,-parkingTarget.l/2,parkingTarget.w,parkingTarget.l);
 ctx.setLineDash([]);ctx.restore();

 obstacles.forEach(o=>{let q=worldToScreen(o.x,o.y);drawCar(q.x,q.y,o.a,{w:o.w,l:o.l,color:"#fff"},false)});
 traffic.forEach(o=>{let q=worldToScreen(o.x,o.y);drawCar(q.x,q.y,o.a,{w:o.w,l:o.l,color:"#fff"},false)});
 let pc=worldToScreen(player.x,player.y);
 drawCar(pc.x,pc.y,player.a,selectedCar,true);

 if(view===1)drawFirstPerson();
}

function drawFirstPerson(){
 const W=canvas.clientWidth,H=canvas.clientHeight;
 ctx.fillStyle="rgba(20,20,20,.22)";ctx.fillRect(0,0,W,H);
 // windshield
 ctx.strokeStyle="rgba(230,230,230,.75)";ctx.lineWidth=7;
 ctx.beginPath();ctx.moveTo(0,H*.18);ctx.lineTo(W*.50,H*.05);ctx.lineTo(W,H*.18);ctx.stroke();
 // dashboard
 ctx.fillStyle="#1b1b1b";ctx.beginPath();ctx.moveTo(0,H*.82);ctx.lineTo(W*.16,H*.72);ctx.lineTo(W*.84,H*.72);ctx.lineTo(W,H*.82);ctx.lineTo(W,H);ctx.lineTo(0,H);ctx.closePath();ctx.fill();
 // mirrors
 for(const side of [-1,1]){
  const x=side<0?W*.10:W*.90;
  ctx.fillStyle="#222";ctx.fillRect(x-38,H*.43,76,48);
  ctx.fillStyle="#7e9ca5";ctx.fillRect(x-30,H*.44,60,30);
  ctx.fillStyle="#eee";ctx.font="10px Arial";ctx.textAlign="center";
  ctx.fillText(side<0?"좌측 사이드미러":"우측 사이드미러",x,H*.44+43);
 }
 ctx.fillStyle="#222";ctx.fillRect(W*.40,H*.20,W*.20,35);
 ctx.fillStyle="#7e9ca5";ctx.fillRect(W*.415,H*.205,W*.17,24);
 ctx.fillStyle="#fff";ctx.font="11px Arial";ctx.textAlign="center";ctx.fillText("백미러",W*.50,H*.205+43);
}

function newMission(){
 result.style.display="none"; running=true; startTime=performance.now(); elapsed=0;
 const c=selectedCar;
 player={x:0,y:0,a:-Math.PI/2,s:0};
 obstacles=[];traffic=[];
 const difficulty=Math.min(stage,10);
 for(let i=0;i<3+difficulty;i++){
  traffic.push({x:(Math.random()-.5)*300,y:(Math.random()*1200)-500,a:Math.random()<.5?Math.PI/2:-Math.PI/2,w:30,l:55});
 }
 if(modeEl.value==="parking" || modeEl.value==="test"){
  const types=[0,Math.PI/2,Math.PI,-Math.PI/2];
  parkingTarget={x:(Math.random()-.5)*150,y:-350-Math.random()*350,a:types[Math.floor(Math.random()*types.length)],w:c.w+42,l:c.l+55};
  // parked cars around target
  const sideGap=c.w+35;
  obstacles.push({x:parkingTarget.x-sideGap,y:parkingTarget.y,a:parkingTarget.a,w:32,l:55});
  obstacles.push({x:parkingTarget.x+sideGap,y:parkingTarget.y,a:parkingTarget.a,w:32,l:55});
 }else{
  parkingTarget={x:0,y:-650,a:-Math.PI/2,w:c.w+42,l:c.l+55};
 }
}

function update(dt){
 if(!running)return;
 elapsed=(performance.now()-startTime)/1000;
 const c=selectedCar;
 if(keys.ArrowUp) player.s=Math.min(player.s+0.10*dt*60,3.4);
 else if(keys.ArrowDown) player.s=Math.max(player.s-0.12*dt*60,-2.0);
 else player.s*=Math.pow(.92,dt*60);
 const steer=(keys.ArrowLeft?-1:0)+(keys.ArrowRight?1:0);
 if(Math.abs(player.s)>.05) player.a+=steer*c.turn*dt*60*(player.s>0?1:-1);
 player.x+=Math.cos(player.a)*player.s*dt*60;
 player.y+=Math.sin(player.a)*player.s*dt*60;

 // simple collision
 for(const o of [...traffic,...obstacles]){
  const dx=player.x-o.x,dy=player.y-o.y;
  if(Math.hypot(dx,dy)<(c.l+o.l)*.32){
   player.s*=.35;
   earned=Math.max(0,earned-1);
  }
 }
 if(modeEl.value==="parking"){
  const dx=player.x-parkingTarget.x,dy=player.y-parkingTarget.y;
  if(Math.hypot(dx,dy)<25 && Math.abs(player.s)<.12 && keys.Space===false){
   // no auto-complete; player must press Enter
  }
 }
}

function angleDiff(a,b){
 let d=Math.abs((a-b)%(Math.PI*2));return d>Math.PI?Math.PI*2-d:d;
}
function finish(){
 if(!running)return;
 running=false;
 const c=selectedCar;
 const dx=player.x-parkingTarget.x,dy=player.y-parkingTarget.y;
 const posErr=Math.hypot(dx,dy);
 const deg=angleDiff(player.a,parkingTarget.a)*180/Math.PI;
 const posAcc=Math.max(0,100-posErr*1.4);
 const angleAcc=Math.max(0,100-deg*1.5);
 const accuracy=Math.max(0,Math.min(100,(posAcc+angleAcc)/2));
 const base=modeEl.value==="parking"?9000:modeEl.value==="test"?14000:6000;
 earned=Math.floor(base*(accuracy/100)*Math.max(.35,1-stage*.025));
 if(deg<8) earned+=3000;
 money+=earned;
 if(accuracy>80 && stage<10)stage++;
 refreshMoney();
 rText.innerHTML=
  `차량: <b>${c.name}</b><br>`+
  `소요 시간: <b>${elapsed.toFixed(2)}초</b><br>`+
  `주차 위치 오차: <b>${posErr.toFixed(1)}</b><br>`+
  `주차 각도 오차: <b>${deg.toFixed(2)}°</b><br>`+
  `주차 정확도: <b>${accuracy.toFixed(1)}%</b><br>`+
  `획득 금액: <b>+${moneyText(earned)}</b>`;
 result.style.display="block";
}

function render(){
 ctx.clearRect(0,0,canvas.clientWidth,canvas.clientHeight);
 drawWorld();
 hud.innerHTML=
  `<b>${modeEl.options[modeEl.selectedIndex].text}</b><br>`+
  `차량: ${selectedCar.name}<br>`+
  `시간: ${elapsed.toFixed(2)}초<br>`+
  `현재 속도: ${Math.abs(player.s*30).toFixed(0)}<br>`+
  `시점: ${view===3?"3인칭":"1인칭"}<br>`+
  `목표: 노란 주차 구역`;
}

function loop(now){
 const dt=Math.min(.04,(now-last)/1000);last=now;
 update(dt);render();requestAnimationFrame(loop);
}
requestAnimationFrame(loop);

window.addEventListener("keydown",e=>{
 if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight"," "].includes(e.key))e.preventDefault();
 keys[e.key]=true;
 if(e.key===" ") {view=view===3?1:3}
 if(e.key==="Enter" && running)finish();
});
window.addEventListener("keyup",e=>{keys[e.key]=false});

modeEl.addEventListener("change",newMission);
carEl.addEventListener("change",()=>{selectedCar=carById(carEl.value);newMission()});
document.getElementById("start").onclick=newMission;
document.getElementById("again").onclick=newMission;
document.getElementById("garageBtn").onclick=()=>{
 garage.style.display="block";renderGarage();
};
document.getElementById("closeGarage").onclick=()=>garage.style.display="none";

function renderGarage(){
 carsEl.innerHTML="";
 cars.forEach(c=>{
  const d=document.createElement("div");d.className="carcard"+(owned.has(c.id)?"":" lock");
  d.innerHTML=`<div class="swatch" style="background:${c.color}"></div>
   <b>${c.name}</b><br><span class="small">${owned.has(c.id)?"보유":"가격 "+moneyText(c.price)}</span><br><br>`;
  const b=document.createElement("button");
  b.textContent=owned.has(c.id)?"선택":"구매";
  b.disabled=owned.has(c.id);
  if(!owned.has(c.id))b.onclick=()=>{
   if(money>=c.price){money-=c.price;owned.add(c.id);refreshMoney();refreshCars();renderGarage();showMsg(c.name+" 구매 완료");}
   else showMsg("돈이 부족합니다");
  };
  d.appendChild(b);carsEl.appendChild(d);
 });
}

refreshCars();refreshMoney();newMission();
</script>
</body>
</html>
"""

st.markdown("## RPG 자동차 주차·도로주행 게임")
st.caption("프로토타입 — 방향키로 운전하고 Space로 시점을 전환하세요. 결과 화면에서 Enter를 누르면 미션을 종료할 수 있습니다.")
components.html(HTML, height=760, scrolling=False)
