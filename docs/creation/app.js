/* ============================================================================
   EchoScroll · Creation Demo · app.js
   3-step flow : upload → edit → output
   ============================================================================ */

(() => {
'use strict';

const $  = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => Array.from(p.querySelectorAll(s));

// ============================================================================
// Data : 4 sample paintings — 周易卦象系列 · 真音乐 (no synthetic)
// ============================================================================
const PAINTINGS = {
  g1: {
    file: '../assets/paintings/gua1_shi.jpg',
    title: '师卦 · 容民畜众', subtitle: '第七卦 · 地水师',
    artist: '《周易》六十四卦系列', dynasty: '现代水墨',
    audio: '../assets/audio/gua1_shi.mp3',
    va: [-0.10, -0.40],
    params: { mode: 'pentatonic 商', instrument: '笙 + 埙 + 低音堂鼓', bpm: '62', dyn: 'p ~ mp' },
    suggestedTags: ['隐逸', '悠远', '水面'],
    markers: [
      { top: '22%', left: '40%', title: '远山笼水汽', v: -0.20, a: -0.30, note: '云气笼罩的远山——埙的低音持续动机自此涌起，对应"水藏地中"。' },
      { top: '70%', left: '58%', title: '网格鱼塘', v: -0.10, a: -0.20, note: '格状田畴是"容民畜众"的视觉化——笙的层叠和声从此展开。' },
      { top: '86%', left: '28%', title: '深墨坡岸', v: -0.30, a: -0.40, note: '前景压底的浓墨坡岸——低音堂鼓如心跳般克制脉动。' },
    ],
  },
  g2: {
    file: '../assets/paintings/gua2_xu.jpg',
    title: '需卦 · 光亨', subtitle: '第五卦 · 水天需',
    artist: '《周易》六十四卦系列', dynasty: '现代水墨',
    audio: '../assets/audio/gua2_xu.mp3',
    va: [+0.45, +0.25],
    params: { mode: 'pentatonic 徵', instrument: '竹笛 + 古筝刮奏 + 琵琶', bpm: '72', dyn: 'mp ~ mf' },
    suggestedTags: ['空灵', '悠远', '宁静'],
    markers: [
      { top: '30%', left: '60%', title: '喷发霞光', v: +0.55, a: +0.50, note: '暖黄赭红的放射状霞光——古筝大刮奏从低到高一路扫开。' },
      { top: '58%', left: '32%', title: '深墨群山', v: +0.10, a: +0.10, note: '黑暗山影积蓄光气——竹笛一句句试探着上扬。' },
      { top: '82%', left: '50%', title: '山影倒映', v: +0.25, a: -0.10, note: '静水中的倒影——二胡 + 碰铃的从容中段，"饮食宴乐"。' },
    ],
  },
  g3: {
    file: '../assets/paintings/gua3_song.jpg',
    title: '讼卦 · 作事谋始', subtitle: '第六卦 · 天水讼',
    artist: '《周易》六十四卦系列', dynasty: '现代水墨',
    audio: '../assets/audio/gua3_song.mp3',
    va: [-0.50, +0.55],
    params: { mode: 'pentatonic 羽', instrument: '二胡 + 板鼓梆子 + 京胡', bpm: '88', dyn: 'mf ~ f' },
    suggestedTags: ['喧嚣'],
    markers: [
      { top: '22%', left: '52%', title: '翻卷乱云', v: -0.40, a: +0.55, note: '天上盘旋绞缠的乱云——板鼓梆子的躁动节奏自此起。' },
      { top: '72%', left: '45%', title: '对冲水纹', v: -0.50, a: +0.50, note: '斜冲交错的浓墨水势——古筝急促轮拨模拟冲突。' },
    ],
  },
  g4: {
    file: '../assets/paintings/gua4_bi.jpg',
    title: '比卦 · 建国亲诸侯', subtitle: '第八卦 · 水地比',
    artist: '《周易》六十四卦系列', dynasty: '现代水墨',
    audio: '../assets/audio/gua4_bi.mp3',
    va: [+0.25, -0.10],
    params: { mode: 'pentatonic 宫', instrument: '古琴 + 古筝 + 箫 + 笙', bpm: '68', dyn: 'p ~ mp' },
    suggestedTags: ['宁静', '悠远', '水面'],
    markers: [
      { top: '20%', left: '40%', title: '远山青翠', v: +0.20, a: -0.05, note: '层叠的远山——箫吹出温润亲和的主题，"亲辅"的和睦。' },
      { top: '55%', left: '52%', title: '水脉交织', v: +0.25, a: -0.10, note: '蜿蜒贯通的水网——古琴 / 古筝流水滚奏连绵不绝。' },
      { top: '78%', left: '62%', title: '青绿洲渚', v: +0.30, a: -0.15, note: '错落相邻的青绿洲渚——笙的暖和声渐入，"建国亲诸侯"。' },
    ],
  },
};

let currentPid = 'g1';
const SELECTED_TAGS = new Set(['隐逸']);

// ============================================================================
// Stage navigation
// ============================================================================
const STAGE_ORDER = ['upload', 'edit', 'output'];
const stageEls = {
  upload: $('#stage-upload'),
  edit:   $('#stage-edit'),
  output: $('#stage-output'),
};

function setStage(name) {
  if (!stageEls[name]) return;
  // 离开输出页时暂停音频
  if (name !== 'output') {
    const a = document.getElementById('audio-el');
    if (a && !a.paused) {
      a.pause();
      const ip = document.querySelector('.ico-play');
      const iu = document.querySelector('.ico-pause');
      if (ip) ip.hidden = false;
      if (iu) iu.hidden = true;
    }
  }
  Object.entries(stageEls).forEach(([n, el]) => {
    el.classList.toggle('active', n === name);
  });
  const idx = STAGE_ORDER.indexOf(name);
  $$('.step').forEach((s, i) => {
    s.classList.toggle('active', i === idx);
    s.classList.toggle('done', i < idx);
  });
  if (name === 'edit') {
    stageEls.edit.classList.remove('revealed');
    setTimeout(() => stageEls.edit.classList.add('revealed'), 120);
  }
  window.scrollTo(0, 0);
}

$$('.step').forEach(btn => {
  btn.addEventListener('click', () => {
    const name = btn.dataset.go;
    if (name === 'output' && currentPid) prepareOutput(currentPid);
    if (name === 'edit')   loadEdit(currentPid);
    setStage(name);
  });
});

$('#brand-home').addEventListener('click', (e) => {
  e.preventDefault();
  setStage('upload');
});

// ============================================================================
// STAGE 1 · Upload
// ============================================================================
const dropZone = $('#upload-drop');
const fileInput = $('#upload-file');

dropZone.addEventListener('click', () => fileInput.click());
dropZone.addEventListener('dragover', (e) => {
  e.preventDefault();
  dropZone.classList.add('drag-over');
});
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', (e) => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  const f = e.dataTransfer.files[0];
  if (f && f.type.startsWith('image/')) handleUpload(f);
});
fileInput.addEventListener('change', () => {
  const f = fileInput.files[0];
  if (f) handleUpload(f);
});

function handleUpload(file) {
  const url = URL.createObjectURL(file);
  PAINTINGS.custom = {
    ...PAINTINGS.p2,
    file: url,
    title: file.name.replace(/\.[^.]+$/, ''),
    artist: 'Your upload',
    dynasty: '—',
  };
  currentPid = 'custom';
  loadEdit('custom');
  if (!sessionStorage.getItem('echoscroll-guide-seen')) {
    setTimeout(() => openGuide(true), 600);
  }
  setStage('edit');
}

$$('.sample-thumb').forEach(t => {
  t.addEventListener('click', () => {
    currentPid = t.dataset.pid;
    loadEdit(currentPid);
    if (!sessionStorage.getItem('echoscroll-guide-seen')) {
      setTimeout(() => openGuide(true), 600);
    }
    setStage('edit');
  });
});

// ============================================================================
// STAGE 2 · Edit
// ============================================================================
function loadEdit(pid) {
  const p = PAINTINGS[pid];
  if (!p) return;
  $('#edit-painting').src = p.file;
  $('#annotation').hidden = true;

  // 动态渲染标记点（每张画自带 markers）
  const wrap = $('.painting-wrap');
  $$('.marker', wrap).forEach(m => m.remove());
  const ann = $('#annotation');
  (p.markers || []).forEach((m) => {
    const btn = document.createElement('button');
    btn.className = 'marker';
    btn.style.top = m.top;
    btn.style.left = m.left;
    btn.dataset.title = m.title;
    btn.dataset.v = (m.v >= 0 ? '+' : '') + m.v.toFixed(2);
    btn.dataset.a = (m.a >= 0 ? '+' : '') + m.a.toFixed(2);
    btn.dataset.note = m.note;
    btn.setAttribute('aria-label', '标记点 · ' + m.title);
    const pulse = document.createElement('span');
    pulse.className = 'm-pulse';
    btn.appendChild(pulse);
    wrap.insertBefore(btn, ann);
  });

  SELECTED_TAGS.clear();
  (p.suggestedTags || []).forEach(t => SELECTED_TAGS.add(t));
  refreshTagButtons();
}

const annotation = $('#annotation');
const annTitle = $('#ann-title');
const annV = $('#ann-v');
const annA = $('#ann-a');
const annNote = $('#ann-note');

// 标记点：用事件代理（markers 是动态生成的）
$('.painting-wrap').addEventListener('click', (e) => {
  const m = e.target.closest('.marker');
  if (!m) return;
  e.stopPropagation();
  const isActive = m.classList.contains('active');
  $$('.marker').forEach(x => x.classList.remove('active'));
  if (isActive) {
    annotation.hidden = true;
    return;
  }
  m.classList.add('active');
  annTitle.textContent = m.dataset.title || '画上标注';
  annV.textContent = m.dataset.v || '+0.00';
  annA.textContent = m.dataset.a || '+0.00';
  annNote.textContent = m.dataset.note || '';
  annotation.hidden = false;
});
$('#ann-close').addEventListener('click', () => {
  annotation.hidden = true;
  $$('.marker').forEach(x => x.classList.remove('active'));
});

function refreshTagButtons() {
  $$('.tag').forEach(b => {
    b.classList.toggle('active', SELECTED_TAGS.has(b.dataset.tag));
  });
}
$$('.tag').forEach(b => {
  b.addEventListener('click', () => {
    const t = b.dataset.tag;
    if (SELECTED_TAGS.has(t)) SELECTED_TAGS.delete(t);
    else SELECTED_TAGS.add(t);
    refreshTagButtons();
  });
});

$('#generate-btn').addEventListener('click', () => {
  prepareOutput(currentPid);
  setStage('output');
});

// ============================================================================
// STAGE 3 · Output
// ============================================================================
const audioEl = $('#audio-el');
const playBtn = $('#play-btn');
const icoPlay = playBtn.querySelector('.ico-play');
const icoPause = playBtn.querySelector('.ico-pause');
const progressFill = $('#progress-fill');
const progressSeal = $('#progress-seal');
const progressWrap = $('#progress-wrap');
const timeDisplay = $('#time-display');
const volBtn = $('#vol-btn');
const volIcon = $('#vol-icon');
const volTrack = $('#vol-track');
const volFill = $('#vol-fill');
const ocToggle = $('#oc-toggle');
const ocEditLayer = $('#oc-edit-layer');
const otShow = ocToggle.querySelector('.ot-show');
const otHide = ocToggle.querySelector('.ot-hide');
const outputPainting = $('#output-painting');
const pcVa = $('#pc-va');
const pcTags = $('#pc-tags');

function prepareOutput(pid) {
  const p = PAINTINGS[pid];
  if (!p) return;
  outputPainting.src = p.file;
  audioEl.src = p.audio;
  audioEl.load();
  resetPlayer();
  pcVa.textContent = `${p.va[0].toFixed(2)}  ·  ${p.va[1].toFixed(2)}`;

  // 注入编辑层 oc-markers (按画作 markers 的位置)
  ocEditLayer.innerHTML = '';
  (p.markers || []).forEach(m => {
    const span = document.createElement('span');
    span.className = 'oc-marker';
    span.style.top = m.top;
    span.style.left = m.left;
    ocEditLayer.appendChild(span);
  });
  const rows = $$('.pc-row strong', $('#param-card'));
  if (rows.length >= 4) {
    rows[0].textContent = p.params.mode;
    rows[1].textContent = p.params.instrument;
    rows[2].textContent = p.params.bpm;
    rows[3].textContent = p.params.dyn;
  }
  pcTags.innerHTML = '';
  SELECTED_TAGS.forEach(t => {
    const span = document.createElement('span');
    span.className = 'pc-tag';
    span.textContent = t;
    pcTags.appendChild(span);
  });
}

function resetPlayer() {
  audioEl.currentTime = 0;
  audioEl.pause();
  progressFill.style.width = '0%';
  progressSeal.style.left = '0%';
  icoPlay.hidden = false;
  icoPause.hidden = true;
  timeDisplay.textContent = '0:00 / 0:00';
}

function fmt(t) {
  if (!Number.isFinite(t)) return '0:00';
  const m = Math.floor(t / 60);
  const s = Math.floor(t % 60).toString().padStart(2, '0');
  return `${m}:${s}`;
}

audioEl.addEventListener('loadedmetadata', () => {
  timeDisplay.textContent = `0:00 / ${fmt(audioEl.duration)}`;
});
audioEl.addEventListener('timeupdate', () => {
  if (!audioEl.duration) return;
  const pct = (audioEl.currentTime / audioEl.duration) * 100;
  progressFill.style.width = pct + '%';
  progressSeal.style.left = pct + '%';
  timeDisplay.textContent = `${fmt(audioEl.currentTime)} / ${fmt(audioEl.duration)}`;
});
audioEl.addEventListener('ended', () => {
  icoPlay.hidden = false;
  icoPause.hidden = true;
});
audioEl.addEventListener('error', () => {
  timeDisplay.textContent = '— 音频加载失败 —';
});

// 点画外区域关闭标注
document.addEventListener('click', (e) => {
  if (!stageEls.edit.classList.contains('active')) return;
  if (!e.target.closest('.marker') && !e.target.closest('.annotation')) {
    annotation.hidden = true;
    $$('.marker').forEach(x => x.classList.remove('active'));
  }
});
// ESC 关闭 modal / 标注
window.addEventListener('keydown', (e) => {
  if (e.key === 'Escape') {
    if (!$('#guide-mask').hidden) { closeGuide(); return; }
    if (!annotation.hidden)       { annotation.hidden = true; $$('.marker').forEach(x => x.classList.remove('active')); return; }
  }
});

playBtn.addEventListener('click', () => {
  if (audioEl.paused) {
    audioEl.play().catch(()=>{});
    icoPlay.hidden = true;
    icoPause.hidden = false;
  } else {
    audioEl.pause();
    icoPlay.hidden = false;
    icoPause.hidden = true;
  }
});

// —— Progress bar : click + drag + keyboard ——
function seekFromEvent(e) {
  if (!audioEl.duration) return;
  const rect = progressWrap.getBoundingClientRect();
  const pt = e.touches ? e.touches[0] : e;
  const ratio = (pt.clientX - rect.left) / rect.width;
  audioEl.currentTime = audioEl.duration * Math.max(0, Math.min(1, ratio));
  // 视觉立即更新（不等 timeupdate）
  const pct = Math.max(0, Math.min(100, ratio * 100));
  progressFill.style.width = pct + '%';
  progressSeal.style.left = pct + '%';
}
let pDrag = false;
progressWrap.addEventListener('mousedown', (e) => {
  pDrag = true;
  progressWrap.classList.add('dragging');
  seekFromEvent(e);
});
window.addEventListener('mousemove', (e) => { if (pDrag) seekFromEvent(e); });
window.addEventListener('mouseup', () => {
  if (pDrag) { pDrag = false; progressWrap.classList.remove('dragging'); }
});
progressWrap.addEventListener('touchstart', (e) => {
  pDrag = true; progressWrap.classList.add('dragging');
  seekFromEvent(e); e.preventDefault();
}, { passive: false });
window.addEventListener('touchmove', (e) => { if (pDrag) { seekFromEvent(e); e.preventDefault(); } }, { passive: false });
window.addEventListener('touchend', () => {
  if (pDrag) { pDrag = false; progressWrap.classList.remove('dragging'); }
});

let lastVolume = 0.7;
audioEl.volume = lastVolume;

function setVolume(v) {
  v = Math.max(0, Math.min(1, v));
  audioEl.volume = v;
  volFill.style.width = (v * 100) + '%';
  if (v === 0)       volIcon.src = 'assets-design/vol_mute.png';
  else if (v < 0.5)  volIcon.src = 'assets-design/vol_mid.png';
  else               volIcon.src = 'assets-design/vol_high.png';
}
setVolume(lastVolume);

volBtn.addEventListener('click', () => {
  if (audioEl.volume > 0) { lastVolume = audioEl.volume; setVolume(0); }
  else setVolume(lastVolume || 0.7);
});

// —— Volume bar : click + drag ——
function setVolFromEvent(e) {
  const rect = volTrack.getBoundingClientRect();
  const pt = e.touches ? e.touches[0] : e;
  const r = (pt.clientX - rect.left) / rect.width;
  setVolume(r);
  if (audioEl.volume > 0) lastVolume = audioEl.volume;
}
let vDrag = false;
volTrack.addEventListener('mousedown', (e) => { vDrag = true; setVolFromEvent(e); });
window.addEventListener('mousemove', (e) => { if (vDrag) setVolFromEvent(e); });
window.addEventListener('mouseup', () => { vDrag = false; });
volTrack.addEventListener('touchstart', (e) => { vDrag = true; setVolFromEvent(e); e.preventDefault(); }, { passive: false });
window.addEventListener('touchmove', (e) => { if (vDrag) { setVolFromEvent(e); e.preventDefault(); } }, { passive: false });
window.addEventListener('touchend', () => { vDrag = false; });

// —— Keyboard shortcuts : space=play/pause, ←/→=seek 5s, ↑/↓=vol ——
window.addEventListener('keydown', (e) => {
  if (e.target.tagName === 'INPUT') return;
  if (!stageEls.output.classList.contains('active')) return;
  switch (e.code) {
    case 'Space':       e.preventDefault(); playBtn.click(); break;
    case 'ArrowLeft':   e.preventDefault(); audioEl.currentTime = Math.max(0, audioEl.currentTime - 5); break;
    case 'ArrowRight':  e.preventDefault(); audioEl.currentTime = Math.min(audioEl.duration || 0, audioEl.currentTime + 5); break;
    case 'ArrowUp':     e.preventDefault(); setVolume(audioEl.volume + 0.05); lastVolume = audioEl.volume; break;
    case 'ArrowDown':   e.preventDefault(); setVolume(audioEl.volume - 0.05); lastVolume = audioEl.volume; break;
  }
});

let layerVisible = true;
ocToggle.addEventListener('click', () => {
  layerVisible = !layerVisible;
  ocEditLayer.classList.toggle('hidden', !layerVisible);
  otShow.hidden = layerVisible;
  otHide.hidden = !layerVisible;
});

// ============================================================================
// GUIDE MODAL
// ============================================================================
const guideMask = $('#guide-mask');
function openGuide(markSeen = false) {
  guideMask.hidden = false;
  if (markSeen) sessionStorage.setItem('echoscroll-guide-seen', '1');
}
function closeGuide() { guideMask.hidden = true; }

$('#help-btn').addEventListener('click', () => openGuide());
$('#guide-close').addEventListener('click', closeGuide);
$('#guide-cta').addEventListener('click', closeGuide);
guideMask.addEventListener('click', (e) => {
  if (e.target === guideMask) closeGuide();
});

// ============================================================================
// INIT
// ============================================================================
setStage('upload');

})();
