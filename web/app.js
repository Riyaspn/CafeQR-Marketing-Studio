let currentCampaign = null;
let currentTab = 'poster';

document.addEventListener('DOMContentLoaded', () => {
  checkMetaStatus();
  loadTrends();
  setupLiveEvaluation();
});

// 1. Check Meta Connection Status
async function checkMetaStatus() {
  const badge = document.getElementById('metaStatusBadge');
  const text = document.getElementById('metaStatusText');
  try {
    const res = await fetch('/api/meta-status');
    const data = await res.json();
    if (data.valid) {
      badge.className = 'status-pill status-connected';
      text.innerText = `🟢 Meta Connected (${data.page_name || 'Cafe QR'})`;
    } else {
      badge.className = 'status-pill status-expired';
      text.innerText = `🔴 Meta Token Expired (Click to update)`;
    }
  } catch (e) {
    badge.className = 'status-pill status-expired';
    text.innerText = `⚠️ Offline / Server error`;
  }
}

// 2. Load Trends from Trend Radar
async function loadTrends() {
  const list = document.getElementById('trendList');
  list.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Scanning Google News RSS for Indian F&B controversies...</p>
    </div>
  `;

  try {
    const res = await fetch('/api/trends');
    const data = await res.json();
    if (data.trends && data.trends.length > 0) {
      list.innerHTML = '';
      data.trends.forEach((t, i) => {
        const item = document.createElement('div');
        item.className = 'trend-item';
        item.onclick = () => selectTrend(t, item);
        item.innerHTML = `
          <span class="trend-badge">${t.category_label || t.category}</span>
          <div class="trend-title">${t.title}</div>
          <div class="trend-meta">
            <span>📰 ${t.source}</span>
            <span>⚡ Click to Draft</span>
          </div>
        `;
        list.appendChild(item);
      });
    } else {
      list.innerHTML = '<p style="padding: 20px; color: #94A3B8;">No trends found. Try refreshing or use a custom topic.</p>';
    }
  } catch (e) {
    list.innerHTML = `<p style="padding: 20px; color: #EF4444;">Failed to fetch trends: ${e.message}</p>`;
  }
}

// 3. Select a Trend and Generate Campaign
async function selectTrend(topic, element) {
  document.querySelectorAll('.trend-item').forEach(el => el.classList.remove('active'));
  if (element) element.classList.add('active');

  showLoading('Analyzing news & generating viral campaign...');

  try {
    const res = await fetch('/api/generate-campaign', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topic,
        voice: document.getElementById('editVoice').value
      })
    });
    const data = await res.json();
    if (data.success && data.campaign) {
      currentCampaign = data.campaign;
      populateEditor(currentCampaign);
      displayPreviews(currentCampaign);
    }
  } catch (e) {
    alert(`Failed to generate campaign: ${e.message}`);
  } finally {
    hideLoading();
  }
}

// 4. Generate from Custom Topic Box
function generateFromCustom() {
  const input = document.getElementById('customTopicInput');
  const text = input.value.trim();
  if (!text) {
    alert('Please enter a topic or controversy hook');
    return;
  }
  const customTopic = {
    title: text,
    source: "Custom Trend Input",
    category: "AGGREGATOR_EXPLOITATION"
  };
  selectTrend(customTopic, null);
}

// 5. Populate Editor Fields
function populateEditor(campaign) {
  document.getElementById('editHeadline').value = campaign.headline || '';
  document.getElementById('editSubtext').value = campaign.subtext || '';
  document.getElementById('editTemplate').value = campaign.template || 'agency_editorial';
  document.getElementById('editScript').value = campaign.script || '';
  document.getElementById('editCaption').value = campaign.caption || '';
  if (campaign.evaluation) {
    updateRubricUI(campaign.evaluation);
  }

  // Populate AI Sound Radar
  if (campaign.audio_profile) {
    const ap = campaign.audio_profile;
    const moodPill = document.getElementById('soundMoodPill');
    if (moodPill) moodPill.innerText = ap.situation ? `🎵 ${ap.situation.replace(/_/g, ' ')}` : '🎵 Dynamic Audio';
    const trackTitle = document.getElementById('soundTrackTitle');
    if (trackTitle) trackTitle.innerText = ap.title || 'Dynamic Commercial Beat';
    const trackGenre = document.getElementById('soundTrackGenre');
    if (trackGenre) trackGenre.innerText = ap.genre || 'CC0 Royalty-Free Audio';
    const igTrack = document.getElementById('soundIgTrack');
    if (igTrack) igTrack.innerText = ap.trending_ig_tip || 'Trending Beat';
    const slider = document.getElementById('bgmVolumeSlider');
    const valText = document.getElementById('bgmVolumeVal');
    const vol = ap.bgm_volume !== undefined ? Math.round(ap.bgm_volume * 100) : 18;
    if (slider) slider.value = vol;
    if (valText) valText.innerText = `${vol}%`;
  }
}

function updateBgmVolume(val) {
  const valText = document.getElementById('bgmVolumeVal');
  if (valText) valText.innerText = `${val}%`;
  if (currentCampaign) {
    if (!currentCampaign.audio_profile) currentCampaign.audio_profile = {};
    currentCampaign.audio_profile.bgm_volume = parseFloat(val) / 100.0;
  }
}

function copyTrendingSound() {
  const igTrack = document.getElementById('soundIgTrack');
  if (igTrack && igTrack.innerText) {
    navigator.clipboard.writeText(igTrack.innerText);
    const btn = document.querySelector('.btn-copy-sound');
    if (btn) {
      btn.innerText = '✅';
      setTimeout(() => { btn.innerText = '📋'; }, 1500);
    }
  }
}

async function searchCustomOnlineSound() {
  const input = document.getElementById('customSoundQuery');
  const query = input ? input.value.trim() : '';
  if (!query) {
    alert('Please enter a sound vibe or instrument (e.g. "cyberpunk electronic", "lofi acoustic guitar", "ambient techno")');
    return;
  }
  showLoading(`Searching online open catalog for "${query}" & downloading fresh track...`);
  try {
    const res = await fetch('/api/search-music', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: query })
    });
    const data = await res.json();
    if (data.success) {
      if (currentCampaign) {
        if (!currentCampaign.audio_profile) currentCampaign.audio_profile = {};
        currentCampaign.audio_profile.search_query = query;
        currentCampaign.audio_profile.title = `Fresh Online Beat: ${query}`;
        currentCampaign.audio_profile.genre = "Dynamic AI Search Match";
        currentCampaign.audio_profile.situation = "CUSTOM_SITUATION";
        populateEditor(currentCampaign);
      }
      alert(`✅ Fresh music found & downloaded!\nTrack: ${data.filename}\nClick "Update Reel" to mix this new track into your video.`);
    } else {
      alert(`Search notice: ${data.error || 'No matching audio found'}`);
    }
  } catch (err) {
    alert(`Error fetching sound: ${err.message}`);
  } finally {
    hideLoading();
  }
}

// 6. Display Previews
function displayPreviews(campaign) {
  // Poster
  if (campaign.poster_url) {
    document.getElementById('posterPlaceholder').classList.add('hidden');
    document.getElementById('posterWrapper').classList.remove('hidden');
    const posterImg = document.getElementById('posterImg');
    posterImg.src = campaign.poster_url + '?t=' + Date.now();
    document.getElementById('posterDownloadLink').href = campaign.poster_url;
  }

  // Reel Video
  if (campaign.reel_url) {
    document.getElementById('reelPlaceholder').classList.add('hidden');
    document.getElementById('reelWrapper').classList.remove('hidden');
    const reelVideo = document.getElementById('reelVideo');
    reelVideo.src = campaign.reel_url + '?t=' + Date.now();
    reelVideo.load();
    document.getElementById('reelDownloadLink').href = campaign.reel_url;
  } else {
    document.getElementById('reelPlaceholder').classList.remove('hidden');
    document.getElementById('reelWrapper').classList.add('hidden');
  }
}

// 7. Re-Render Poster
async function reRenderPoster() {
  if (!currentCampaign) return;

  currentCampaign.headline = document.getElementById('editHeadline').value;
  currentCampaign.subtext = document.getElementById('editSubtext').value;
  currentCampaign.template = document.getElementById('editTemplate').value;

  showLoading('Rendering high-res poster (1080x1350)...');
  try {
    const res = await fetch('/api/render-poster', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ creative: currentCampaign })
    });
    const data = await res.json();
    if (data.success) {
      currentCampaign.poster_url = data.poster_url;
      currentCampaign.poster_file = data.poster_file;
      if (data.evaluation) {
        currentCampaign.evaluation = data.evaluation;
        updateRubricUI(data.evaluation);
      }
      displayPreviews(currentCampaign);
      switchPreviewTab('poster');
    }
  } catch (e) {
    alert(`Render failed: ${e.message}`);
  } finally {
    hideLoading();
  }
}

// 8. Re-Render Reel Video
async function reRenderReel() {
  if (!currentCampaign) return;

  currentCampaign.headline = document.getElementById('editHeadline').value;
  currentCampaign.subtext = document.getElementById('editSubtext').value;
  currentCampaign.script = document.getElementById('editScript').value;
  const voice = document.getElementById('editVoice').value;

  showLoading('Synthesizing neural voiceover & encoding MP4 Reel...');
  try {
    const res = await fetch('/api/render-reel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ creative: currentCampaign, voice: voice })
    });
    const data = await res.json();
    if (data.success) {
      currentCampaign.reel_url = data.reel_url;
      currentCampaign.reel_file = data.reel_file;
      displayPreviews(currentCampaign);
      switchPreviewTab('reel');
    } else {
      alert(`Reel generation error: ${data.error}`);
    }
  } catch (e) {
    alert(`Reel render failed: ${e.message}`);
  } finally {
    hideLoading();
  }
}

// 9. 1-Click Approve & Publish to Meta
async function publishApprovedCampaign() {
  if (!currentCampaign) {
    alert('Please generate or select a campaign first.');
    return;
  }

  const pubFb = document.getElementById('pubFacebook').checked;
  const pubIg = document.getElementById('pubInstagram').checked;
  const caption = document.getElementById('editCaption').value;
  const feedback = document.getElementById('publishStatus');
  const btn = document.getElementById('publishBtn');

  if (!pubFb && !pubIg) {
    alert('Please select at least one publishing platform (Facebook or Instagram).');
    return;
  }

  btn.disabled = true;
  btn.innerText = '⏳ PUBLISHING TO META API...';
  feedback.className = 'publish-feedback';
  feedback.classList.remove('hidden');
  feedback.innerText = 'Connecting to Meta Graph API...';

  try {
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_path: currentCampaign.poster_file,
        video_path: currentCampaign.reel_file,
        caption: caption,
        facebook: pubFb,
        instagram: pubIg
      })
    });
    const data = await res.json();
    if (data.success && data.results) {
      let msg = '';
      let allSuccess = true;
      data.results.forEach(r => {
        if (r.success) {
          msg += `✅ ${r.platform}: Published successfully! (ID: ${r.post_id})\n`;
        } else {
          allSuccess = false;
          msg += `❌ ${r.platform}: ${r.error || 'Failed'}\n`;
        }
      });
      feedback.className = `publish-feedback ${allSuccess ? 'success' : 'error'}`;
      feedback.innerText = msg;
    }
  } catch (e) {
    feedback.className = 'publish-feedback error';
    feedback.innerText = `Publishing error: ${e.message}`;
  } finally {
    btn.disabled = false;
    btn.innerText = 'APPROVE & PUBLISH TO SOCIAL MEDIA';
  }
}

// 10. Switch Preview Tabs
function switchPreviewTab(tab) {
  currentTab = tab;
  document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
  document.getElementById('posterTab').classList.add('hidden');
  document.getElementById('reelTab').classList.add('hidden');
  document.getElementById('draftsTab').classList.add('hidden');

  if (tab === 'poster') {
    document.querySelectorAll('.tab-btn')[0].classList.add('active');
    document.getElementById('posterTab').classList.remove('hidden');
  } else if (tab === 'reel') {
    document.querySelectorAll('.tab-btn')[1].classList.add('active');
    document.getElementById('reelTab').classList.remove('hidden');
  } else if (tab === 'drafts') {
    document.querySelectorAll('.tab-btn')[2].classList.add('active');
    document.getElementById('draftsTab').classList.remove('hidden');
  }
}

// 11. Load Drafts Gallery
async function loadDraftsGallery() {
  switchPreviewTab('drafts');
  const grid = document.getElementById('draftsGrid');
  grid.innerHTML = '<div class="spinner"></div>';
  try {
    const res = await fetch('/api/drafts');
    const data = await res.json();
    grid.innerHTML = '';
    if (data.drafts && data.drafts.length > 0) {
      data.drafts.forEach(d => {
        const card = document.createElement('div');
        card.className = 'draft-item-card';
        card.style.cssText = 'background: #151C2C; padding: 12px; border-radius: 12px; border: 1px solid #26334D; display: flex; flex-direction: column; gap: 8px; align-items: center;';
        if (d.type === 'image') {
          card.innerHTML = `<img src="${d.url}" style="max-height: 140px; border-radius: 8px;" /><a href="${d.url}" target="_blank" style="color: #FF7A00; font-size: 12px;">${d.name}</a>`;
        } else if (d.type === 'video') {
          card.innerHTML = `<video src="${d.url}" style="max-height: 140px; border-radius: 8px;" controls></video><a href="${d.url}" target="_blank" style="color: #FF7A00; font-size: 12px;">${d.name}</a>`;
        }
        grid.appendChild(card);
      });
    } else {
      grid.innerHTML = '<p style="color: #94A3B8;">No drafts saved yet.</p>';
    }
  } catch (e) {
    grid.innerHTML = '<p style="color: #EF4444;">Failed to load drafts.</p>';
  }
}

// Copy Caption Helper
function copyCaptionToClipboard() {
  const cap = document.getElementById('editCaption').value;
  navigator.clipboard.writeText(cap);
  alert('Caption & hashtags copied to clipboard!');
}

// Modal Helpers
function openSettingsModal() {
  document.getElementById('settingsModal').classList.remove('hidden');
}
function closeSettingsModal() {
  document.getElementById('settingsModal').classList.add('hidden');
}
async function saveSettings() {
  const token = document.getElementById('cfgMetaToken').value.trim();
  const gemini = document.getElementById('cfgGeminiKey').value.trim();
  const phone = document.getElementById('cfgWhatsAppPhone').value.trim();
  const status = document.getElementById('settingsSaveStatus');

  try {
    const res = await fetch('/api/update-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        meta_token: token,
        gemini_key: gemini,
        whatsapp_phone: phone
      })
    });
    const data = await res.json();
    if (data.success) {
      status.className = 'save-status success';
      status.classList.remove('hidden');
      status.innerText = 'Settings saved to .env! Verifying Meta status...';
      setTimeout(() => {
        closeSettingsModal();
        checkMetaStatus();
      }, 1500);
    }
  } catch (e) {
    status.className = 'save-status error';
    status.classList.remove('hidden');
    status.innerText = `Save failed: ${e.message}`;
  }
}

// Loading Spinner Helpers
function showLoading(msg) {
  const el = document.getElementById('loadingIndicator');
  const txt = document.getElementById('spinnerText');
  txt.innerText = msg;
  el.classList.remove('hidden');
}
function hideLoading() {
  document.getElementById('loadingIndicator').classList.add('hidden');
}

// 9. Viral Rubric Evaluator Helpers
function updateRubricUI(evaluation) {
  if (!evaluation) return;

  const pill = document.getElementById('rubricScorePill');
  const score = evaluation.score || 0;
  const grade = evaluation.grade || 'SOLID_ENGAGING';

  pill.innerText = `${score} / 10.0 • ${grade.replace('_', ' ')}`;
  pill.className = 'rubric-score-pill';
  if (score >= 8.5) pill.classList.add('grade-viral');
  else if (score >= 7.0) pill.classList.add('grade-solid');
  else pill.classList.add('grade-needs-work');

  const b = evaluation.breakdown || {};
  const setBar = (valId, fillId, val, maxVal) => {
    const v = typeof val === 'number' ? val : 0;
    const elVal = document.getElementById(valId);
    const elFill = document.getElementById(fillId);
    if (elVal) elVal.innerText = `${v.toFixed(1)} / ${maxVal.toFixed(1)}`;
    if (elFill) elFill.style.width = `${Math.min(100, Math.round((v / maxVal) * 100))}%`;
  };

  setBar('scoreHook', 'fillHook', b.hook_velocity, 2.0);
  setBar('scoreMath', 'fillMath', b.empirical_proof, 2.0);
  setBar('scoreContrast', 'fillContrast', b.contrast_ratio, 2.0);
  setBar('scoreEase', 'fillEase', b.cognitive_ease, 2.0);
  setBar('scoreCTA', 'fillCTA', b.cta_urgency, 2.0);

  const tipsContainer = document.getElementById('rubricTips');
  if (tipsContainer) {
    tipsContainer.innerHTML = '';
    const recs = evaluation.recommendations || [];
    if (recs.length === 0 || (recs.length === 1 && recs[0].includes('perfectly optimized'))) {
      tipsContainer.innerHTML = '<div class="tip-pill">💡 Creative perfectly aligned with Hormozi &amp; Schwartz viral rules.</div>';
    } else {
      recs.forEach(r => {
        const item = document.createElement('div');
        item.className = 'tip-pill warning';
        item.innerText = `⚡ ${r}`;
        tipsContainer.appendChild(item);
      });
    }
  }
}

function toggleRubricDetails() {
  const details = document.getElementById('rubricDetails');
  const arrow = document.getElementById('rubricToggleArrow');
  if (details.classList.contains('hidden')) {
    details.classList.remove('hidden');
    arrow.classList.remove('open');
  } else {
    details.classList.add('hidden');
    arrow.classList.add('open');
  }
}

let liveEvalDebounce = null;
function setupLiveEvaluation() {
  ['editHeadline', 'editSubtext', 'editScript', 'editCaption'].forEach(id => {
    const el = document.getElementById(id);
    if (el) {
      el.addEventListener('input', () => {
        clearTimeout(liveEvalDebounce);
        liveEvalDebounce = setTimeout(triggerLiveEvaluation, 400);
      });
    }
  });
}

async function triggerLiveEvaluation() {
  const payload = {
    headline: document.getElementById('editHeadline').value,
    subtext: document.getElementById('editSubtext').value,
    script: document.getElementById('editScript').value,
    caption: document.getElementById('editCaption').value
  };

  try {
    const res = await fetch('/api/evaluate-copy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ creative: payload })
    });
    const data = await res.json();
    if (data.success && data.evaluation) {
      if (currentCampaign) currentCampaign.evaluation = data.evaluation;
      updateRubricUI(data.evaluation);
    }
  } catch (e) {
    console.warn('Live evaluation error:', e);
  }
}

// 10. Autonomous Competitor & Hook Harvester
async function harvestIntel() {
  showLoading('🌾 Crawling competitor feeds & harvesting viral angles into Vault...');
  try {
    const res = await fetch('/api/harvest-intel', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.success) {
      alert(`🌾 Harvester Complete!\n\nAdded: ${data.result.new_swipes_count} new high-converting hooks\nTotal Vault Swipes: ${data.result.total_swipes}`);
      loadTrends();
    } else {
      alert('Harvester failed.');
    }
  } catch (e) {
    alert(`Harvester error: ${e.message}`);
  } finally {
    hideLoading();
  }
}
