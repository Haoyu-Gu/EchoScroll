/* ============================================================================
   EchoScroll · Creation Demo · app.js
   3-step flow : upload → edit → output
   ============================================================================ */

(() => {
'use strict';

const $  = (s, p = document) => p.querySelector(s);
const $$ = (s, p = document) => Array.from(p.querySelectorAll(s));

// ============================================================================
// Data : 4 sample paintings
// ============================================================================
const PAINTINGS = {
  p1: {
    file: '../assets/paintings/p1_miyouren_cloudy_mountains.jpg',
    title: '云山图', artist: 'Mi Youren · 米友仁', dynasty: '南宋',
    audio: '../assets/audio/real_p1_va_neg.mp3',
    va: [-0.22, -0.55],
    params: { mode: 'pentatonic 羽', instrument: 'guqin + xiao', bpm: '≈ 50', dyn: 'pp ~ p' },
    suggestedTags: ['宁静', '悠远', '隐逸'],
  },
  p2: {
    file: '../assets/paintings/p2_dujin_poet_lin_bu.jpg',
    title: '林逋月夜行吟', artist: 'Du Jin · 杜堇', dynasty: '明',
    audio: '../assets/audio/real_p5_va_neg.mp3',
    va: [-0.03, 0.11],
    params: { mode: 'pentatonic 宫', instrument: 'guqin + xiao', bpm: '≈ 60', dyn: 'p ~ mp' },
    suggestedTags: ['宁静', '空灵'],
  },
  p5: {
    file: '../assets/paintings/p5_bada_landscape.jpg',
    title: '仿郭忠恕山水', artist: 'Bada Shanren · 八大山人', dynasty: '清',
    audio: '../assets/audio/real_p5_va_neg.mp3',
    va: [-0.42, 0.18],
    params: { mode: 'pentatonic 羽', instrument: 'guqin solo + 古筝', bpm: '≈ 70', dyn: 'p' },
    suggestedTags: ['隐逸', '空灵', '悠远'],
  },
  p6: {
    file: '../assets/paintings/p6_streams_mountains.jpg',
    title: '溪山无尽图', artist: 'Anonymous · 佚名', dynasty: '北宋-金',
    audio: '../assets/audio/real_p1_va_pos.mp3',
    va: [-0.05, 0.45],
    params: { mode: 'pentatonic 徵', instrument: 'erhu + guzheng + 鼓', bpm: '≈ 84', dyn: 'mf ~ f' },
    suggestedTags: ['喧嚣', '悠远'],
  },
};

let currentPid = 'p2';
const SELECTED_TAGS = new Set(['宁静']);

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
  $$('.marker').forEach(m => m.classList.remove('active'));
  SELECTED_TAGS.clear();
  (p.suggestedTags || []).forEach(t => SELECTED_TAGS.add(t));
  refreshTagButtons();
}

const annotation = $('#annotation');
const annTitle = $('#ann-title');
const annV = $('#ann-v');
const annA = $('#ann-a');
const annNote = $('#ann-note');

$$('.marker').forEach(m => {
  m.addEventListener('click', (e) => {
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
