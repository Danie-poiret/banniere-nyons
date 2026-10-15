(function(factory){
  'use strict';
  if(typeof module==='object'&&module.exports){module.exports=factory();}
  else {factory().mount(document);}
})(function(){
  'use strict';
  function integer(value,max){
    if(value===''||value===null||value===undefined)throw new RangeError('Indique un nombre entier dans chaque case.');
    var n=Number(value);
    if(!Number.isSafeInteger(n)||n<0||n>max)throw new RangeError('Utilise des nombres entiers : 0 à 99 personnes par catégorie, 0 à 20 parasols.');
    return n;
  }
  function calculate(input){
    var a=integer(input.adults,99),c=integer(input.children,99),b=integer(input.babies,99),p=integer(input.parasols,20);
    var late=input.arrival==='late',resident=input.resident===true;
    var adult=resident?(late?200:350):(late?350:800);
    var child=resident?(late?200:350):(late?300:600);
    var total=a*adult+c*child+p*300;
    var alternate=resident&&c>0?a*adult+c*(late?150:300)+p*300:null;
    return {adults:a,children:c,babies:b,parasols:p,adultRate:adult,childRate:child,total:total,alternate:alternate,late:late,resident:resident};
  }
  function mount(doc){
    var form=doc.getElementById('nyon-budget');if(!form)return;
    var total=doc.getElementById('nyon-total'),line=doc.getElementById('nyon-breakdown'),alternative=doc.getElementById('nyon-alternative'),error=doc.getElementById('nyon-error');
    var euro=new Intl.NumberFormat('fr-FR',{style:'currency',currency:'EUR'});
    function money(cents){return euro.format(cents/100);}
    function update(){
      try {
        var r=calculate({adults:form.elements.adults.value,children:form.elements.children.value,babies:form.elements.babies.value,parasols:form.elements.parasols.value,arrival:form.elements.arrival.value,resident:form.elements.resident.checked});
        total.textContent=money(r.total);error.hidden=true;error.textContent='';
        line.textContent=r.adults+' adulte(s) × '+money(r.adultRate)+' + '+r.children+' enfant(s) de 6–15 ans × '+money(r.childRate)+' + '+r.babies+' enfant(s) de moins de 6 ans gratuit(s)'+(r.parasols?' + '+r.parasols+' parasol(s) × 3 €':'')+' · '+(r.late?'après 17 h 30':'entrée habituelle')+'.';
        alternative.hidden=r.alternate===null;
        alternative.textContent=r.alternate===null?'':'Attention : avec les tarifs enfants du PDF municipal « Tarifs privilégiés 2026 », le total serait de '+money(r.alternate)+'. Les deux sources municipales diffèrent : fais confirmer le tarif nyonsais enfant à la mairie.';
      }catch(e){total.textContent='—';line.textContent='Le montant sera affiché après correction.';alternative.hidden=true;alternative.textContent='';error.hidden=false;error.textContent=e.message;}
    }
    form.addEventListener('input',update);form.addEventListener('change',update);
    form.addEventListener('submit',function(event){event.preventDefault();update();});
    update();
  }
  return {calculate:calculate,mount:mount};
});
