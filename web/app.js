let currentCampaign = null;
let currentTab = 'poster';

document.addEventListener('DOMContentLoaded', () => {
  checkMetaStatus();
  checkTelegramStatus();
  loadTrends();
  setupLiveEvaluation();
  
  // Session Persistence: restore active working draft if user refreshed the page
  const savedSession = sessionStorage.getItem('cafeqr_active_campaign');
  if (savedSession) {
    try {
      currentCampaign = JSON.parse(savedSession);
      populateEditor(currentCampaign);
      displayPreviews(currentCampaign);
      switchPreviewTab('poster');
      return;
    } catch (e) {
      console.log('Error parsing session campaign:', e);
    }
  }
  // If visiting fresh, check if server has an autonomous draft available without overwriting
  checkServerDraftAvailability();
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

// 1b. Check Telegram Alert Bot Health
async function checkTelegramStatus() {
  const badge = document.getElementById('tgStatusBadge');
  const text = document.getElementById('tgStatusText');
  if (!badge || !text) return;
  try {
    const res = await fetch('/api/telegram-status');
    const data = await res.json();
    if (data.configured && data.valid) {
      badge.className = 'status-pill status-connected';
      text.innerText = `🤖 TG Bot: @${data.bot.username || 'Active'}`;
    } else if (data.configured && !data.valid) {
      badge.className = 'status-pill status-expired';
      text.innerText = `⚠️ TG Token Invalid`;
    } else {
      badge.className = 'status-pill status-expired';
      text.innerText = `⚪ TG Bot Setup`;
    }
  } catch (e) {
    badge.className = 'status-pill status-expired';
    text.innerText = `⚪ TG Offline`;
  }
}

// 1c. Load Latest Auto-Generated Campaign Draft (On-Demand)
async function loadLatestDraft() {
  showLoading('Loading saved server draft...');
  try {
    const res = await fetch('/api/latest-draft');
    const data = await res.json();
    if (data.success && data.draft) {
      currentCampaign = data.draft;
      sessionStorage.setItem('cafeqr_active_campaign', JSON.stringify(currentCampaign));
      populateEditor(currentCampaign);
      displayPreviews(currentCampaign);
      switchPreviewTab('poster');
    } else {
      alert('No previous server draft found.');
    }
  } catch (e) {
    console.log('No previous auto-draft found:', e);
  } finally {
    hideLoading();
  }
}

// 1d. Check Server Draft Availability without overwriting user screen
async function checkServerDraftAvailability() {
  try {
    const res = await fetch('/api/latest-draft');
    const data = await res.json();
    if (data.success && data.draft) {
      const placeholder = document.getElementById('posterPlaceholder');
      if (placeholder && (!currentCampaign || !currentCampaign.poster_url)) {
        placeholder.innerHTML = `
          <div class="empty-icon">🎨</div>
          <h3>Studio Ready</h3>
          <p>Click any trending headline on the left or type a custom topic to generate a fresh viral poster.</p>
          <div style="margin-top: 16px;">
            <button class="btn btn-secondary btn-sm" onclick="loadLatestDraft()" title="Load last autonomous post">
              <span>⚡</span> Load Last Server Draft: "${(data.draft.headline || 'Saved Post').slice(0, 36)}..."
            </button>
          </div>
        `;
      }
    }
  } catch (e) {
    // silent
  }
}

// 1e. Clear Active Workspace Session
function clearCurrentSession() {
  sessionStorage.removeItem('cafeqr_active_campaign');
  currentCampaign = null;
  window.location.reload();
}

let allTrends = [];

// 2. Load Trends from Multi-Vertical Trend Radar
async function loadTrends() {
  const list = document.getElementById('trendList');
  list.innerHTML = `
    <div class="loading-state">
      <div class="spinner"></div>
      <p>Scanning 26 Multi-Vertical Streams across India...</p>
    </div>
  `;

  try {
    const res = await fetch('/api/trends');
    const data = await res.json();
    if (data.trends && data.trends.length > 0) {
      allTrends = data.trends;
      const filterVal = document.getElementById('verticalFilter') ? document.getElementById('verticalFilter').value : 'all';
      renderTrendsList(filterVal);
    } else {
      list.innerHTML = '<p style="padding: 20px; color: #94A3B8;">No trends found. Try refreshing or use a custom topic.</p>';
    }
  } catch (e) {
    list.innerHTML = `<p style="padding: 20px; color: #EF4444;">Failed to fetch trends: ${e.message}</p>`;
  }
}

function filterTrendsByVertical(vertical) {
  renderTrendsList(vertical);
}

function renderTrendsList(vertical) {
  const list = document.getElementById('trendList');
  list.innerHTML = '';
  const filtered = (!vertical || vertical === 'all')
    ? allTrends
    : allTrends.filter(t => (t.vertical || '').toLowerCase().includes(vertical.toLowerCase()));

  if (filtered.length === 0) {
    list.innerHTML = '<p style="padding: 20px; color: #94A3B8;">No stories found in this vertical. Try another or enter a custom topic above.</p>';
    return;
  }

  filtered.forEach((t) => {
    const item = document.createElement('div');
    item.className = 'trend-item';
    item.onclick = () => selectTrend(t, item);
    item.innerHTML = `
      <div style="display: flex; gap: 6px; align-items: center; margin-bottom: 6px; flex-wrap: wrap;">
        <span class="trend-badge">${t.category_label || t.category}</span>
        <span style="font-size: 11px; background: rgba(255,255,255,0.06); padding: 2px 8px; border-radius: 6px; color: #94A3B8;">🏷️ ${t.vertical || 'Multi-Vertical'}</span>
      </div>
      <div class="trend-title">${t.title}</div>
      <div class="trend-meta">
        <span>📰 ${t.source}</span>
        <span>⚡ Click to Draft</span>
      </div>
    `;
    list.appendChild(item);
  });
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
      sessionStorage.setItem('cafeqr_active_campaign', JSON.stringify(currentCampaign));
      populateEditor(currentCampaign);
      displayPreviews(currentCampaign);
      if (window.innerWidth <= 1024) {
        scrollToStudioSection('previewSection');
      }
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

// 4b. Reverse-Engineer Viral URL (yt-dlp + whisper + AI remastering)
async function reverseEngineerFromUrl() {
  const input = document.getElementById('viralUrlInput');
  const url = input.value.trim();
  if (!url) {
    alert('Please enter a valid Instagram Reel, YouTube Shorts, or video URL');
    return;
  }
  const vertical = document.getElementById('verticalFilter') ? document.getElementById('verticalFilter').value : 'Restaurants & Cafes';

  showLoading('Fetching video via yt-dlp, transcribing speech with Whisper & reverse-engineering viral hook...');
  try {
    const res = await fetch('/api/reverse-engineer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url, vertical: vertical })
    });
    const data = await res.json();
    if (data.success && data.campaign) {
      currentCampaign = data.campaign;
      sessionStorage.setItem('cafeqr_active_campaign', JSON.stringify(currentCampaign));
      populateEditor(currentCampaign);
      displayPreviews(currentCampaign);
      switchPreviewTab('poster');
      const intel = currentCampaign.reverse_intel || {};
      alert(`✅ Viral Reverse-Engineering Succeeded!\n\n• Hook Pattern: ${intel.hook_formula || 'Direct Response'}\n• Archetype: ${intel.recommended_visual_archetype || 'Custom'}\n\nRemastered poster generated for Cafe QR!`);
    } else {
      alert(`Reverse-engineering error: ${data.error || 'Failed to process video URL'}`);
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  } finally {
    hideLoading();
  }
}

// 5. Populate Editor Fields
function populateEditor(campaign) {
  document.getElementById('editHeadline').value = campaign.headline || '';
  document.getElementById('editSubtext').value = campaign.subtext || '';
  document.getElementById('editTemplate').value = campaign.template || (campaign.poster_html ? 'freeform_ai' : 'agency_editorial');
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

    const dockMusic = document.getElementById('dockMusicTitle');
    if (dockMusic) {
      dockMusic.innerText = ap.trending_ig_tip || 'Trending Commercial Beat';
    }
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
      sessionStorage.setItem('cafeqr_active_campaign', JSON.stringify(currentCampaign));
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
      sessionStorage.setItem('cafeqr_active_campaign', JSON.stringify(currentCampaign));
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

// 9. 1-Click Approve & Publish to Meta (Facebook Page, Instagram Feed & Story)
async function publishApprovedCampaign() {
  if (!currentCampaign) {
    alert('Please generate or select a campaign first.');
    return;
  }

  const pubFb = document.getElementById('pubFacebook').checked;
  const pubFbStory = document.getElementById('pubFacebookStory') ? document.getElementById('pubFacebookStory').checked : false;
  const pubIg = document.getElementById('pubInstagram').checked;
  const pubStory = document.getElementById('pubStory') ? document.getElementById('pubStory').checked : false;
  const pubThreads = document.getElementById('pubThreads') ? document.getElementById('pubThreads').checked : false;
  const caption = document.getElementById('editCaption').value;
  const feedback = document.getElementById('publishStatus');
  const btn = document.getElementById('publishBtn');

  if (!pubFb && !pubFbStory && !pubIg && !pubStory && !pubThreads) {
    alert('Please select at least one publishing platform.');
    return;
  }

  btn.disabled = true;
  btn.innerText = '⏳ PUBLISHING TO SOCIAL PLATFORMS...';
  feedback.className = 'publish-feedback';
  feedback.classList.remove('hidden');
  feedback.innerText = 'Connecting to Meta Graph API...';

  try {
    const res = await fetch('/api/publish', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        image_path: currentCampaign ? (currentCampaign.poster_file || currentCampaign.poster_path) : null,
        video_path: currentCampaign ? (currentCampaign.reel_file || currentCampaign.reel_path) : null,
        caption: caption,
        facebook: pubFb,
        facebook_story: pubFbStory,
        instagram: pubIg,
        story: pubStory,
        threads: pubThreads,
        public_media_url: (currentCampaign && currentCampaign.poster_url) ? (window.location.origin + currentCampaign.poster_url) : ''
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
      if (data.cleaned_up) {
        msg += `🗑️ Image automatically purged from cloud storage.\n`;
      }
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
    const res = await fetch('/api/saved-campaigns');
    const data = await res.json();
    grid.innerHTML = '';
    if (data.campaigns && data.campaigns.length > 0) {
      data.campaigns.forEach((camp, idx) => {
        const card = document.createElement('div');
        card.className = 'draft-item-card';
        card.style.cssText = 'background: #151C2C; padding: 14px; border-radius: 12px; border: 1px solid #26334D; display: flex; flex-direction: column; gap: 10px;';
        
        const posterSrc = camp.poster_url || '';
        const headline = camp.headline || 'Cafe QR Campaign';
        const vertical = camp.target_vertical || 'Multi-Vertical';
        const date = camp.created_at || 'Recent';

        card.innerHTML = `
          <div style="position: relative; width: 100%; border-radius: 8px; overflow: hidden; background: #0B0F19; display: flex; justify-content: center; align-items: center;">
            <img src="${posterSrc}" style="max-height: 180px; width: auto; object-fit: contain; cursor: pointer;" onclick="loadSpecificCampaign(${idx})" />
            <span style="position: absolute; top: 8px; left: 8px; background: rgba(0,0,0,0.7); font-size: 11px; padding: 2px 8px; border-radius: 4px; color: #FF7A00; font-weight: 700;">🏷️ ${vertical}</span>
          </div>
          <div style="font-weight: 700; font-size: 13px; color: #F8FAFC; line-height: 1.3;">${headline}</div>
          <div style="font-size: 11px; color: #94A3B8;">🕒 Generated: ${date}</div>
          <div style="display: flex; gap: 8px; margin-top: auto;">
            <button class="btn btn-primary btn-sm" onclick="loadSpecificCampaign(${idx})" style="flex: 1; padding: 6px; font-size: 12px;">⚡ Load &amp; Approve</button>
            <a href="${posterSrc}" download="${camp.headline || 'poster'}.png" class="btn btn-secondary btn-sm" style="padding: 6px 10px;" title="Download PNG">⬇️</a>
            <button class="btn btn-secondary btn-sm" onclick="deleteDraftFromCloud(${idx})" style="padding: 6px 10px; color: #EF4444;" title="Purge from cloud">🗑️</button>
          </div>
        `;
        grid.appendChild(card);
      });
      window.cachedSavedCampaigns = data.campaigns;
    } else {
      grid.innerHTML = '<p style="color: #94A3B8; padding: 20px;">No autonomous campaigns saved yet. Click any news headline on the left to generate one!</p>';
    }
  } catch (e) {
    grid.innerHTML = '<p style="color: #EF4444; padding: 20px;">Failed to load saved campaigns.</p>';
  }
}

function loadSpecificCampaign(idx) {
  if (window.cachedSavedCampaigns && window.cachedSavedCampaigns[idx]) {
    const camp = window.cachedSavedCampaigns[idx];
    currentCampaign = camp;
    populateEditor(camp);
    displayPreviews(camp);
    switchPreviewTab('poster');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  }
}

async function deleteDraftFromCloud(idx) {
  if (!window.cachedSavedCampaigns || !window.cachedSavedCampaigns[idx]) return;
  const camp = window.cachedSavedCampaigns[idx];
  if (!confirm(`Permanently delete "${camp.headline || 'this draft'}" from cloud storage?`)) return;

  try {
    const res = await fetch('/api/delete-draft', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        poster_path: camp.poster_path,
        poster_url: camp.poster_url
      })
    });
    const data = await res.json();
    if (data.success) {
      loadDraftsGallery();
    }
  } catch (e) {
    alert(`Failed to delete draft: ${e.message}`);
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

async function testTelegramAlert() {
  const status = document.getElementById('settingsSaveStatus');
  status.className = 'save-status';
  status.classList.remove('hidden');
  status.innerText = 'Dispatching test ping to your Telegram bot...';

  try {
    const res = await fetch('/api/test-telegram', { method: 'POST' });
    const data = await res.json();
    if (data.success) {
      status.className = 'save-status success';
      status.innerText = '✅ Test alert delivered to your Telegram! Check your app.';
      checkTelegramStatus();
    } else {
      status.className = 'save-status error';
      status.innerText = `❌ Delivery failed: ${data.error || 'Check Bot Token & Chat ID'}`;
    }
  } catch (e) {
    status.className = 'save-status error';
    status.innerText = `Error: ${e.message}`;
  }
}

async function saveSettings() {
  const token = document.getElementById('cfgMetaToken').value.trim();
  const gemini = document.getElementById('cfgGeminiKey').value.trim();
  const phone = document.getElementById('cfgWhatsAppPhone').value.trim();
  const tgToken = document.getElementById('cfgTelegramToken') ? document.getElementById('cfgTelegramToken').value.trim() : '';
  const tgChat = document.getElementById('cfgTelegramChatId') ? document.getElementById('cfgTelegramChatId').value.trim() : '';
  const studioUrl = document.getElementById('cfgStudioUrl') ? document.getElementById('cfgStudioUrl').value.trim() : '';
  const status = document.getElementById('settingsSaveStatus');

  try {
    const res = await fetch('/api/update-settings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        meta_token: token,
        gemini_key: gemini,
        whatsapp_phone: phone,
        telegram_token: tgToken,
        telegram_chat_id: tgChat,
        studio_url: studioUrl
      })
    });
    const data = await res.json();
    if (data.success) {
      status.className = 'save-status success';
      status.classList.remove('hidden');
      status.innerText = 'Settings saved to .env! Verifying Meta & Telegram connections...';
      setTimeout(() => {
        closeSettingsModal();
        checkMetaStatus();
        checkTelegramStatus();
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

// 11. Trigger Autonomous Poster Cycle & Telegram Alert On-Demand
async function triggerAutonomousCycle() {
  showLoading('🤖 Running Autonomous Poster Cycle: scanning 26 news streams, generating campaign & dispatching Telegram alert...');
  try {
    const res = await fetch('/api/trigger-cron', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({})
    });
    const data = await res.json();
    if (data.success) {
      alert('🚀 Autonomous Poster Cycle Triggered!\n\nYour AI Agent is generating the campaign in the cloud and will ping your Telegram bot momentarily.\n\nClick "Latest Draft" in 10-15 seconds to view it here.');
      setTimeout(loadLatestDraft, 12000);
    } else {
      alert(`Notice: ${data.message || 'Cycle could not start'}`);
    }
  } catch (e) {
    alert(`Trigger error: ${e.message}`);
  } finally {
    hideLoading();
  }
}

// 12. Mobile & Multi-Device Quick Navigation
function scrollToStudioSection(sectionId, btn) {
  const target = document.getElementById(sectionId);
  if (target) {
    const navBar = document.getElementById('mobileQuickNav');
    const navOffset = (navBar && window.getComputedStyle(navBar).display !== 'none') ? navBar.offsetHeight + 10 : 0;
    const bodyRect = document.body.getBoundingClientRect().top;
    const elementRect = target.getBoundingClientRect().top;
    const elementPosition = elementRect - bodyRect;
    const offsetPosition = elementPosition - navOffset;

    window.scrollTo({
      top: Math.max(0, offsetPosition),
      behavior: 'smooth'
    });

    document.querySelectorAll('.quick-nav-pill').forEach(b => b.classList.remove('active'));
    if (btn) {
      btn.classList.add('active');
    } else {
      const activeBtn = document.querySelector(`.quick-nav-pill[data-target="${sectionId}"]`);
      if (activeBtn) activeBtn.classList.add('active');
    }
  }
}

// Active section spy for mobile quick-nav
window.addEventListener('scroll', () => {
  if (window.innerWidth > 1024) return;
  const sections = ['radarSection', 'previewSection', 'editorSection'];
  const scrollPos = window.scrollY + 120;
  for (const id of sections) {
    const el = document.getElementById(id);
    if (el) {
      const top = el.offsetTop;
      const height = el.offsetHeight;
      if (scrollPos >= top && scrollPos < top + height) {
        document.querySelectorAll('.quick-nav-pill').forEach(b => {
          b.classList.toggle('active', b.getAttribute('data-target') === id);
        });
        break;
      }
    }
  }
}, { passive: true });
