import { useEffect, useState } from 'react'
import { NavLink, Route, Routes, useNavigate } from 'react-router-dom'
import { motion, AnimatePresence } from 'framer-motion'
import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis } from 'recharts'
import i18n from 'i18next'
import { initReactI18next, useTranslation } from 'react-i18next'

const copy = {
  ar: { translation: { home:'الرئيسية', measure:'قِياس', history:'السجلات', more:'المزيد', hello:'مرحباً، أحمد', today:'اليوم', measureNow:'قِس ضغطك الآن', status:'نتيجتك جيدة', statusText:'ابقَ هادئاً واستمر في العلاج.', last:'آخر قياس', mmhg:'ملم زئبق', bpm:'نبضة / د', reminder:'تذكير بالغذاء', reminderText:'قلّل الملح اليوم', instructions:'تعليمات القياس', sit:'اجلس بهدوء لمدة 5 دقائق', arm:'ضع الذراع على الطاولة', wait:'لا تتحرك ولا تتحدث', save:'حفظ القياس', saved:'تم حفظ القياس', newReading:'قياس جديد', systolic:'القيمة العليا', diastolic:'القيمة السفلى', pulse:'نبضات القلب', historyTitle:'سجلاتك', week:'هذا الأسبوع', normal:'طبيعي', elevated:'مرتفع قليلاً', doctor:'تواصل مع الطبيب', caregiver:'المتابعة العائلية', dark:'الوضع الليلي', language:'اللغة', offline:'يعمل بدون إنترنت' } },
  fr: { translation: { home:'Accueil', measure:'Mesurer', history:'Historique', more:'Plus', hello:'Bonjour, Ahmed', today:"Aujourd'hui", measureNow:'Mesurer ma tension', status:'Votre tension est bonne', statusText:'Restez calme et continuez votre suivi.', last:'Dernière mesure', mmhg:'mm Hg', bpm:'batt./min', reminder:'Conseil du jour', reminderText:'Réduisez le sel aujourd’hui', instructions:'Comment mesurer', sit:'Asseyez-vous calmement 5 minutes', arm:'Posez le bras sur la table', wait:'Ne bougez pas et ne parlez pas', save:'Enregistrer', saved:'Mesure enregistrée', newReading:'Nouvelle mesure', systolic:'Valeur haute', diastolic:'Valeur basse', pulse:'Pouls', historyTitle:'Vos mesures', week:'Cette semaine', normal:'Normal', elevated:'Un peu élevé', doctor:'Contacter le médecin', caregiver:'Suivi familial', dark:'Mode sombre', language:'Langue', offline:'Fonctionne hors ligne' } },
  en: { translation: { home:'Home', measure:'Measure', history:'History', more:'More', hello:'Hello, Ahmed', today:'Today', measureNow:'Measure my blood pressure', status:'Your reading is good', statusText:'Stay calm and keep following your care plan.', last:'Latest reading', mmhg:'mm Hg', bpm:'beats/min', reminder:'Today’s reminder', reminderText:'Reduce salt in your meals', instructions:'How to measure', sit:'Sit quietly for 5 minutes', arm:'Rest your arm on a table', wait:'Stay still and do not talk', save:'Save reading', saved:'Reading saved', newReading:'New reading', systolic:'Top number', diastolic:'Bottom number', pulse:'Pulse', historyTitle:'Your readings', week:'This week', normal:'Normal', elevated:'A little high', doctor:'Contact doctor', caregiver:'Family follow-up', dark:'Dark mode', language:'Language', offline:'Works offline' } },
}

i18n.use(initReactI18next).init({ resources: copy, lng: localStorage.getItem('lang') || 'fr', fallbackLng: 'fr', interpolation: { escapeValue: false } })

type IconName = 'home'|'heart'|'chart'|'more'|'moon'|'mic'|'check'|'bell'|'user'|'doctor'|'language'|'wifi'
function Icon({ name, size=26 }: {name:IconName, size?:number}) {
  const paths: Record<IconName, React.ReactNode> = {
    home:<><path d="M3 11.5 12 4l9 7.5"/><path d="M5 10v10h14V10"/><path d="M9 20v-6h6v6"/></>,
    heart:<path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 21l7.8-7.6a5.5 5.5 0 0 0 1-8.8Z"/>, chart:<><path d="M4 19V9"/><path d="M10 19V5"/><path d="M16 19v-7"/><path d="M22 19H2"/></>,
    more:<><circle cx="5" cy="12" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="19" cy="12" r="1.5"/></>, moon:<path d="M21 12.8A9 9 0 1 1 11.2 3 7 7 0 0 0 21 12.8Z"/>, mic:<><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3M8 21h8"/></>, check:<path d="m5 12 4 4L19 6"/>,
    bell:<><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9"/><path d="M10 21h4"/></>, user:<><circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/></>, doctor:<><path d="M4 3v6a4 4 0 0 0 8 0V3M4 3h3M9 3h3"/><path d="M8 13v3a4 4 0 0 0 8 0v-2"/><circle cx="18" cy="12" r="3"/><path d="m18 15-1 4"/></>, language:<><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a15 15 0 0 1 0 18M12 3a15 15 0 0 0 0 18"/></>, wifi:<><path d="M5 12.5a10 10 0 0 1 14 0M8.5 16a5 5 0 0 1 7 0"/><circle cx="12" cy="20" r="1"/></>
  }
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>
}

const readings = [{day:'Mon',value:118},{day:'Tue',value:124},{day:'Wed',value:121},{day:'Thu',value:116},{day:'Fri',value:119},{day:'Sat',value:122},{day:'Sun',value:118}]

function speak(text:string) { if ('speechSynthesis' in window) { speechSynthesis.cancel(); const u = new SpeechSynthesisUtterance(text); u.lang = i18n.language === 'ar' ? 'ar-DZ' : i18n.language === 'fr' ? 'fr-DZ' : 'en-US'; speechSynthesis.speak(u) } }

function Header({dark,setDark}:{dark:boolean,setDark:(v:boolean)=>void}) {
  const {t} = useTranslation(); const navigate = useNavigate()
  const changeLanguage = () => { const next = i18n.language === 'fr' ? 'ar' : i18n.language === 'ar' ? 'en' : 'fr'; i18n.changeLanguage(next); localStorage.setItem('lang', next); document.documentElement.dir = next === 'ar' ? 'rtl' : 'ltr'; document.documentElement.lang = next }
  return <header className="app-header"><button className="brand" onClick={()=>navigate('/')} aria-label="TensiGuard DZ"><span className="brand-mark"><Icon name="heart"/></span><span><strong>TensiGuard</strong><small>DZ</small></span></button><div className="header-actions"><button className="icon-button" onClick={changeLanguage} aria-label={t('language')} title={t('language')}><Icon name="language"/></button><button className="icon-button" onClick={()=>setDark(!dark)} aria-label={t('dark')}><Icon name="moon"/></button></div></header>
}

function Home() {
  const {t}=useTranslation(); const navigate=useNavigate()
  return <main className="page home-page"><section className="welcome"><div><p className="eyebrow">{t('today')} · 30 mai</p><h1>{t('hello')} 👋</h1></div><div className="offline"><Icon name="wifi" size={18}/>{t('offline')}</div></section>
    <motion.button whileTap={{scale:.98}} className="measure-cta" onClick={()=>navigate('/measure')}><span className="pulse-icon"><Icon name="heart" size={42}/></span><span>{t('measureNow')}<small>● ● ●</small></span><span className="arrow">›</span></motion.button>
    <section className="status-card"><div className="status-icon"><Icon name="check" size={28}/></div><div><h2>{t('status')}</h2><p>{t('statusText')}</p></div></section>
    <section className="reading-card"><div className="card-heading"><div><p>{t('last')}</p><h2>118 <span>/ 78</span></h2><small>{t('mmhg')}</small></div><div className="status-pill">{t('normal')}</div></div><div className="mini-chart"><ResponsiveContainer width="100%" height="100%"><AreaChart data={readings}><defs><linearGradient id="blueFill" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#1677d2" stopOpacity={.35}/><stop offset="95%" stopColor="#1677d2" stopOpacity={0}/></linearGradient></defs><XAxis dataKey="day" axisLine={false} tickLine={false}/><Tooltip/><Area type="monotone" dataKey="value" stroke="#1677d2" strokeWidth={3} fill="url(#blueFill)"/></AreaChart></ResponsiveContainer></div><div className="reading-meta"><span>72 {t('bpm')}</span><span>08:42</span></div></section>
    <section className="tip-card"><span><Icon name="bell"/></span><div><strong>{t('reminder')}</strong><p>{t('reminderText')}</p></div></section></main>
}

function Measure() {
  const {t}=useTranslation(); const navigate=useNavigate(); const [saved,setSaved]=useState(false)
  const save=()=>{setSaved(true); speak(t('saved')); setTimeout(()=>navigate('/'),1000)}
  return <main className="page"><div className="page-title-row"><button className="back" onClick={()=>navigate(-1)}>‹</button><h1>{t('newReading')}</h1><button className="sound" onClick={()=>speak(`${t('instructions')}. ${t('sit')}. ${t('arm')}. ${t('wait')}`)} aria-label="Voice instructions"><Icon name="mic"/></button></div>
    <AnimatePresence>{saved&&<motion.div initial={{opacity:0,y:-10}} animate={{opacity:1,y:0}} exit={{opacity:0}} className="toast"><Icon name="check"/> {t('saved')}</motion.div>}</AnimatePresence>
    <section className="instruction-card"><h2>{t('instructions')}</h2>{[t('sit'),t('arm'),t('wait')].map((x,i)=><div className="instruction" key={x}><span>{i+1}</span><p>{x}</p></div>)}</section>
    <section className="entry-card"><label>{t('systolic')}<div className="number-entry"><button aria-label="Decrease">−</button><strong>118</strong><button aria-label="Increase">+</button></div></label><label>{t('diastolic')}<div className="number-entry"><button aria-label="Decrease">−</button><strong>78</strong><button aria-label="Increase">+</button></div></label><label>{t('pulse')}<div className="number-entry compact"><strong>72</strong><span>{t('bpm')}</span></div></label></section>
    <button className="save-button" onClick={save}><Icon name="check"/>{t('save')}</button></main>
}

function History(){const {t}=useTranslation();return <main className="page"><h1>{t('historyTitle')}</h1><section className="history-summary"><div><span>{t('week')}</span><strong>118 / 78</strong><small>{t('normal')}</small></div><div className="donut">86%</div></section><section className="history-list">{[["30 mai","118 / 78","08:42","normal"],["29 mai","122 / 80","08:38","elevated"],["28 mai","116 / 76","08:45","normal"]].map(x=><article key={x[0]}><div className={`history-dot ${x[3]}`} /><div><strong>{x[0]}</strong><small>{x[2]}</small></div><b>{x[1]}</b><span>{t(x[3] as 'normal'|'elevated')}</span></article>)}</section></main>}

function More(){const {t}=useTranslation();const [darkLocal,setDarkLocal]=useState(false);return <main className="page"><h1>{t('more')}</h1><section className="profile-card"><div className="avatar"><Icon name="user" size={32}/></div><div><strong>Ahmed Benali</strong><small>67 ans · Alger</small></div></section><div className="menu-list"><button><span><Icon name="doctor"/></span><b>{t('doctor')}</b><i>›</i></button><button><span><Icon name="user"/></span><b>{t('caregiver')}</b><i>›</i></button><button onClick={()=>setDarkLocal(!darkLocal)}><span><Icon name="moon"/></span><b>{t('dark')}</b><div className={`toggle ${darkLocal?'on':''}`} /></button><button><span><Icon name="language"/></span><b>{t('language')}</b><i>›</i></button></div></main>}

function App({dark,setDark}:{dark:boolean,setDark:(v:boolean)=>void}) {
  const {t}=useTranslation(); useEffect(()=>{const lang=localStorage.getItem('lang')||'fr'; i18n.changeLanguage(lang); document.documentElement.dir=lang==='ar'?'rtl':'ltr';document.documentElement.lang=lang},[])
  const tabs=[{to:'/',icon:'home' as IconName,label:t('home')},{to:'/measure',icon:'heart' as IconName,label:t('measure')},{to:'/history',icon:'chart' as IconName,label:t('history')},{to:'/more',icon:'more' as IconName,label:t('more')}]
  return <div className="app-shell"><Header dark={dark} setDark={setDark}/><Routes><Route path="/" element={<Home/>}/><Route path="/measure" element={<Measure/>}/><Route path="/history" element={<History/>}/><Route path="/more" element={<More/>}/></Routes><nav className="bottom-nav" aria-label="Main navigation">{tabs.map(x=><NavLink key={x.to} to={x.to} end={x.to==='/' } className={({isActive})=>isActive?'active':''}><span><Icon name={x.icon}/></span>{x.label}</NavLink>)}</nav></div>
}
export default App
