import{r as l,l as E,j as t,c as w}from"./vendor-C0yZRDJS.js";import{r as y}from"./index.json-BYPkOlfB.js";import{c as M}from"./everything.json-BGTX2m8U.js";(function(){const n=document.createElement("link").relList;if(n&&n.supports&&n.supports("modulepreload"))return;for(const e of document.querySelectorAll('link[rel="modulepreload"]'))a(e);new MutationObserver(e=>{for(const r of e)if(r.type==="childList")for(const d of r.addedNodes)d.tagName==="LINK"&&d.rel==="modulepreload"&&a(d)}).observe(document,{childList:!0,subtree:!0});function c(e){const r={};return e.integrity&&(r.integrity=e.integrity),e.referrerPolicy&&(r.referrerPolicy=e.referrerPolicy),e.crossOrigin==="use-credentials"?r.credentials="include":e.crossOrigin==="anonymous"?r.credentials="omit":r.credentials="same-origin",r}function a(e){if(e.ep)return;e.ep=!0;const r=c(e);fetch(e.href,r)}})();function O(){const o=l.useMemo(()=>E.Index.load(y),[]),[n,c]=l.useState(""),a=l.useMemo(()=>{const s=new Map;return M.forEach(i=>{s.set(i.detail_url,i)}),s},[]),e=l.useMemo(()=>{if(!n)return null;try{return o.search(n)}catch{return[]}},[o,n]),r=l.useMemo(()=>e?e.map(s=>{const i=s.ref;return a.get(i)}):M,[e,a]),d=l.useMemo(()=>{const s=new Map;return e&&(e.forEach(i=>{const u=i.ref,f=i.matchData.metadata;Object.entries(f).forEach(([p,m])=>{Object.entries(m).forEach(([x,{position:N}])=>{N.forEach(([g,j])=>{console.log({ref:u,term:p,field:x,pos:[g,j]});const b=s.get(u)??[];b.push({ref:u,term:p,field:x,pos:[g,j]}),s.set(u,b)})})})}),console.log([...s.entries()])),s},[e]);return t.jsx(t.Fragment,{children:t.jsxs("div",{className:"p-1",children:[t.jsx("div",{className:"mb-3 w-full text-center p-3",children:t.jsx("input",{onChange:s=>c(s.target.value),className:"border w-full max-w-[600px] h-8 text-lg px-1"})}),t.jsxs("div",{className:"space-y-2",children:[r.length===0&&t.jsx(t.Fragment,{children:"No results found."}),r.map(s=>t.jsx(_,{company:s,matches:d.get(s.detail_url)??[]},s.detail_url))]})]})})}function h(o,n,c){return l.useMemo(()=>{if(!c)return t.jsx(t.Fragment,{});const a=o.filter(e=>e.field===n);if(a){let e=0;const r=a.map(d=>{const{pos:s}=d,[i,u]=s,f=i+u,p=c.substring(e,i),m=c.substring(i,f);return e=f,t.jsxs("span",{children:[p,t.jsx("span",{className:"bg-amber-300 rounded",children:m})]},`${s}`)});return r.push(t.jsx("span",{children:c.substring(e)},"end")),r}return t.jsx("span",{children:c})},[o,c,n])}function _({company:o,matches:n}){var r,d;const c=h(n,"name",o.name),a=h(n,"description",(r=o.details)==null?void 0:r.description),e=h(n,"products_manufactured",(d=o.details)==null?void 0:d.products_manufactured);return t.jsxs("div",{className:"p-1 border rounded w-fit",children:[t.jsx("a",{href:o.detail_url,target:"_blank",className:"text-lg underline text-blue-600",children:c}),t.jsxs("div",{children:[t.jsx("div",{className:"font-bold",children:"Description"}),a]}),t.jsxs("div",{children:[t.jsx("div",{className:"font-bold",children:"Products Manufactured"}),e]})]},o.detail_url)}w.createRoot(document.getElementById("root")).render(t.jsx(O,{}));
