let startX = 0;
let startY = 0;
let currentX = 0;
let currentY = 0;

function submitSwipeAction(message, source, action) {
  const form = document.createElement("form");
  form.method = "POST";
  form.action = "/message-action";

  ["message","source","action"].forEach((k,i)=>{
    const input=document.createElement("input");
    input.type="hidden";
    input.name=k;
    input.value=[message,source,action][i];
    form.appendChild(input);
  });

  document.body.appendChild(form);
  form.submit();
}

function riskScore(msg){
  let score=20;
  msg=msg.toLowerCase();

  ["bonus","free","para","kazan","link","casino"].forEach(w=>{
    if(msg.includes(w)) score+=10;
  });

  if(msg.includes("http")) score+=15;
  return Math.min(score,100);
}

function openModal(msg){
  document.getElementById("detailModal").classList.add("show");
  document.getElementById("detailMessage").innerText=msg;
  document.getElementById("detailRisk").innerText="Risk: "+riskScore(msg);
}

function closeDetailModal(){
  document.getElementById("detailModal").classList.remove("show");
}
window.closeDetailModal=closeDetailModal;

document.querySelectorAll(".card").forEach(card=>{

  card.addEventListener("touchstart",e=>{
    startX=e.touches[0].clientX;
    startY=e.touches[0].clientY;
  });

  card.addEventListener("touchmove",e=>{
    currentX=e.touches[0].clientX;
    currentY=e.touches[0].clientY;

    let dx=currentX-startX;
    let dy=currentY-startY;

    if(Math.abs(dx)>Math.abs(dy)){
      card.style.transform=`translateX(${dx}px)`;
      card.style.background=dx>0?"rgba(255,0,0,0.3)":"rgba(0,255,0,0.3)";
    } else if(dy<0){
      card.style.transform=`translateY(${dy}px)`;
    }
  });

  card.addEventListener("touchend",()=>{
    let dx=currentX-startX;
    let dy=currentY-startY;

    let msg=card.dataset.message;
    let src=card.dataset.source;

    if(dx>120){
      submitSwipeAction(msg,src,"spam");
    }
    else if(dx<-120){
      submitSwipeAction(msg,src,"clean");
    }
    else if(dy<-100){
      openModal(msg);
    }

    card.style.transform="none";
    card.style.background="#0d2018";
  });

});
