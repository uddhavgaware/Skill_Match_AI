/**
 * SkillMatch AI - Production Web Application Engine
 * Handles semantic resume uploads, competency radar mapping, What-If simulation,
 * interactive recommendations, live job applications, and recruiter talent workflows.
 */

// Self-contained API Base (Zero-configuration: automatic same-origin or localhost)
const API_BASE = (window.location.protocol === "file:" || !window.location.origin || window.location.origin === "null")
  ? "http://localhost:8000"
  : "";

// Initial candidate profile helper
function getInitialProfile() {
  const saved = localStorage.getItem("skillmatch_candidate_profile");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed && parsed.extracted_skills && parsed.extracted_skills.length > 0) {
        return parsed;
      }
    } catch (e) {}
  }
  return {
    id: "candidate-live",
    name: "Alex Chen",
    email: "alex.chen@berkeley.edu",
    education: "B.S. in Electrical Engineering & Computer Science, UC Berkeley",
    extracted_skills: ["Python", "PyTorch", "Transformers", "Machine Learning", "Deep Learning", "Computer Vision", "Scikit-Learn", "Git", "Docker", "FastAPI"],
    links: { github: "https://github.com/alexchen-ai", linkedin: "https://linkedin.com/in/alexchen-ai" },
    experience_summary: "Undergraduate Researcher at Berkeley AI Research (BAIR)",
    radar_pillars: { "AI & ML": 98.0, "Fullstack": 42.0, "Data & Analytics": 15.0, "Cloud & DevOps": 64.0, "Systems & CS": 64.0, "UI/UX & Product": 15.0 }
  };
}

// Global Application State
const state = {
  profile: getInitialProfile(),
  recommendations: [],
  allInternships: [],
  myApplications: [],
  activeDomain: "all",
  activeWorkType: "all",
  minMatchScore: 0,
  activeTab: "match-studio",
  selectedJobForGap: null,
  simulatedSkillsToAdd: [],
  radarChartInstance: null,
  activeApplyingJob: null
};

// Initialize Application
document.addEventListener("DOMContentLoaded", async () => {
  // Init Radar Canvas
  state.radarChartInstance = new RadarChart("skillRadarCanvas");

  // Setup DOM Event Listeners
  setupNavigation();
  setupIngestionTabs();
  setupDragAndDrop();
  setupFilters();
  setupAddSkill();
  setupModals();
  setupProfileEditor();
  setupApplyFlow();
  setupPostJobFlow();

  // Initial candidate profile render
  updateCandidateProfile(state.profile, false);

  // Fetch Initial Data
  await loadAllInternships();
  await fetchMarketTrends();
  await fetchRecommendations();
});

// Toast Utility
function showToast(message, type = "info") {
  const container = document.getElementById("toastContainer");
  if (!container) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  const icon = type === "success" ? "✓" : (type === "error" ? "⚠" : "ℹ");
  toast.innerHTML = `<span>${icon}</span> <span>${message}</span>`;
  container.appendChild(toast);
  setTimeout(() => {
    toast.style.opacity = "0";
    toast.style.transform = "translateX(100%)";
    toast.style.transition = "all 0.3s ease";
    setTimeout(() => toast.remove(), 300);
  }, 3500);
}

// Navigation Tabs
function setupNavigation() {
  const navBtns = document.querySelectorAll(".nav-btn");
  navBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      const tabTarget = btn.getAttribute("data-tab");
      switchTab(tabTarget);
    });
  });
}

function switchTab(tabId) {
  state.activeTab = tabId;
  document.querySelectorAll(".nav-btn").forEach(b => {
    b.classList.toggle("active", b.getAttribute("data-tab") === tabId);
  });

  // Toggle tab views
  const views = {
    "match-studio": document.getElementById("matchStudioView"),
    "gap-studio": document.getElementById("gapStudioView"),
    "directory": document.getElementById("directoryView"),
    "my-applications": document.getElementById("myApplicationsView"),
    "recruiter-hub": document.getElementById("recruiterHubView"),
    "market-trends": document.getElementById("marketView")
  };

  Object.entries(views).forEach(([id, elem]) => {
    if (elem) {
      if (id === tabId) {
        elem.style.display = id === "match-studio" ? "grid" : "block";
      } else {
        elem.style.display = "none";
      }
    }
  });

  // Re-draw radar chart if returning to studio
  if (tabId === "match-studio" && state.radarChartInstance) {
    setTimeout(() => state.radarChartInstance.resize(), 50);
  }

  // Load contextual data for tab
  if (tabId === "gap-studio" && !state.selectedJobForGap && state.recommendations.length > 0) {
    loadJobIntoGapStudio(state.recommendations[0].internship);
  } else if (tabId === "my-applications") {
    loadMyApplications();
  } else if (tabId === "recruiter-hub") {
    loadRecruiterHub();
  }
}

// Ingestion Switcher (Upload vs Paste)
function setupIngestionTabs() {
  const uploadTabBtn = document.getElementById("tabUploadBtn");
  const pasteTabBtn = document.getElementById("tabPasteBtn");
  const dropzone = document.getElementById("dropzoneContainer");
  const pasteZone = document.getElementById("pasteContainer");

  uploadTabBtn?.addEventListener("click", () => {
    uploadTabBtn.classList.add("active");
    pasteTabBtn?.classList.remove("active");
    dropzone.style.display = "block";
    pasteZone.style.display = "none";
  });

  pasteTabBtn?.addEventListener("click", () => {
    pasteTabBtn.classList.add("active");
    uploadTabBtn?.classList.remove("active");
    dropzone.style.display = "none";
    pasteZone.style.display = "block";
  });

  // Paste form submit
  document.getElementById("parseTextBtn")?.addEventListener("click", async () => {
    const text = document.getElementById("resumeTextInput")?.value;
    if (!text || text.trim().length < 20) {
      showToast("Please paste a comprehensive resume or coursework text.", "error");
      return;
    }
    await parseResumeText(text);
  });
}

// Drag & Drop File Handling
function setupDragAndDrop() {
  const dropzone = document.getElementById("dropzoneContainer");
  const fileInput = document.getElementById("fileInput");

  if (!dropzone || !fileInput) return;

  dropzone.addEventListener("click", () => fileInput.click());

  dropzone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropzone.classList.add("dragover");
  });

  dropzone.addEventListener("dragleave", () => {
    dropzone.classList.remove("dragover");
  });

  dropzone.addEventListener("drop", async (e) => {
    e.preventDefault();
    dropzone.classList.remove("dragover");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await uploadResumeFile(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener("change", async (e) => {
    if (e.target.files && e.target.files.length > 0) {
      await uploadResumeFile(e.target.files[0]);
    }
  });
}

// Upload File API Call with resilient error handling & retry
async function uploadResumeFile(file) {
  if (!file) return;

  const validExtensions = [".pdf", ".docx", ".doc", ".txt"];
  const lowerName = file.name.toLowerCase();
  const isValid = validExtensions.some(ext => lowerName.endsWith(ext));
  if (!isValid) {
    showToast("Unsupported file type. Please upload a PDF, DOCX, or TXT resume.", "error");
    return;
  }

  showToast(`Parsing ${file.name}...`, "info");
  const formData = new FormData();
  formData.append("file", file);

  try {
    const uploadUrl = API_BASE ? `${API_BASE}/api/upload-resume` : "/api/upload-resume";
    const res = await fetch(uploadUrl, {
      method: "POST",
      body: formData
    });

    if (!res.ok) {
      let detailMsg = "";
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) detailMsg = errJson.detail;
      } catch (e) {}
      throw new Error(detailMsg || `Upload failed (${res.status})`);
    }

    const data = await res.json();
    updateCandidateProfile(data.profile, true);
    state.recommendations = data.recommendations || [];
    renderRecommendations();
    
    const skillCount = (data.profile && data.profile.extracted_skills) ? data.profile.extracted_skills.length : 0;
    showToast(`✓ Successfully mapped ${skillCount} skills from ${file.name}!`, "success");
  } catch (err) {
    console.error("Upload error:", err);
    showToast(`Upload error: ${err.message || "Failed to process resume"}`, "error");
  }
}

// Parse Raw Text API Call with resilient error handling & retry
async function parseResumeText(text) {
  if (!text || !text.trim()) {
    showToast("Please enter or paste resume/coursework text first.", "error");
    return;
  }

  showToast("Analyzing resume text...", "info");
  try {
    const parseUrl = `${API_BASE}/api/parse-text`;
    const res = await fetch(parseUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text })
    });

    if (!res.ok) {
      let detailMsg = "";
      try {
        const errJson = await res.json();
        if (errJson && errJson.detail) detailMsg = errJson.detail;
      } catch (e) {}
      throw new Error(detailMsg || `Analysis failed (${res.status})`);
    }

    const data = await res.json();
    updateCandidateProfile(data.profile, true);
    state.recommendations = data.recommendations || [];
    renderRecommendations();
    
    const count = (data.profile && data.profile.extracted_skills) ? data.profile.extracted_skills.length : 0;
    showToast(`✓ Successfully extracted ${count} skills!`, "success");
  } catch (err) {
    console.error("Text analysis error:", err);
    showToast(`Error analyzing text: ${err.message || "Failed to process"}`, "error");
  }
}

// Update Candidate Profile in State, UI, and LocalStorage
function updateCandidateProfile(profile, persist = true) {
  state.profile = profile;
  if (persist) {
    try {
      localStorage.setItem("skillmatch_candidate_profile", JSON.stringify(profile));
    } catch (e) {}
  }
  
  // Update sidebar
  const nameElem = document.getElementById("candidateName");
  const eduElem = document.getElementById("candidateEducation");
  const avatarElem = document.getElementById("candidateAvatar");
  const headerName = document.getElementById("headerUserName");
  const headerAvatar = document.getElementById("headerUserAvatar");

  const displayName = profile.name || "Candidate Profile";
  if (nameElem) nameElem.textContent = displayName;
  if (eduElem) eduElem.textContent = profile.education || "Undergraduate Student";
  if (avatarElem) avatarElem.textContent = (displayName).charAt(0).toUpperCase();

  // Update header profile badge
  if (headerName) headerName.textContent = displayName;
  if (headerAvatar) headerAvatar.textContent = (displayName).charAt(0).toUpperCase();

  // Links
  const linksContainer = document.getElementById("candidateLinks");
  if (linksContainer) {
    linksContainer.innerHTML = "";
    if (profile.links?.github) {
      linksContainer.innerHTML += `<a href="${profile.links.github}" target="_blank" class="link-tag"><span>⌥</span> GitHub</a>`;
    }
    if (profile.links?.linkedin) {
      linksContainer.innerHTML += `<a href="${profile.links.linkedin}" target="_blank" class="link-tag"><span>⌘</span> LinkedIn</a>`;
    }
  }

  // Render Skill Cloud Tags
  renderSkillTags();

  // Update Radar Chart
  if (state.radarChartInstance && profile.radar_pillars) {
    state.radarChartInstance.updatePillars(profile.radar_pillars);
  }
}

// Render Skill Tags Cloud
function renderSkillTags() {
  const container = document.getElementById("skillTagsCloud");
  const countBadge = document.getElementById("skillsCountBadge");
  if (!container) return;

  container.innerHTML = "";
  countBadge.textContent = `${state.profile.extracted_skills.length} Skills`;

  state.profile.extracted_skills.forEach(skill => {
    const tag = document.createElement("span");
    tag.className = "skill-tag";
    tag.innerHTML = `
      <span>${skill}</span>
      <span class="skill-tag-remove" data-skill="${skill}" title="Remove skill">&times;</span>
    `;
    tag.querySelector(".skill-tag-remove").addEventListener("click", () => {
      removeSkill(skill);
    });
    container.appendChild(tag);
  });
}

// Add Custom Skill
function setupAddSkill() {
  const input = document.getElementById("newSkillInput");
  const btn = document.getElementById("addSkillBtn");

  const handleAdd = () => {
    const skill = input?.value?.trim();
    if (skill && !state.profile.extracted_skills.includes(skill)) {
      state.profile.extracted_skills.push(skill);
      updateCandidateProfile(state.profile, true);
      if (input) input.value = "";
      fetchRecommendations();
      showToast(`Added '${skill}' to your skillset`, "info");
    }
  };

  btn?.addEventListener("click", handleAdd);
  input?.addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleAdd();
  });
}

function removeSkill(skill) {
  state.profile.extracted_skills = state.profile.extracted_skills.filter(s => s !== skill);
  updateCandidateProfile(state.profile, true);
  fetchRecommendations();
}

// Fetch Recommendations API
async function fetchRecommendations() {
  try {
    const res = await fetch(`${API_BASE}/api/recommend`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        skills: state.profile.extracted_skills,
        experience_summary: state.profile.experience_summary || "",
        education: state.profile.education || "",
        domain: state.activeDomain,
        work_type: state.activeWorkType,
        min_match: state.minMatchScore,
        top_k: 15
      })
    });
    if (!res.ok) throw new Error("Recommendations request failed");
    const data = await res.json();
    state.recommendations = data.recommendations;
    
    // Update radar pillars returned
    if (state.radarChartInstance && data.radar_pillars) {
      state.radarChartInstance.updatePillars(data.radar_pillars);
    }

    renderRecommendations();
  } catch (err) {
    console.error("Error fetching recommendations:", err);
  }
}

// Render Recommendation Cards
function renderRecommendations() {
  const container = document.getElementById("recCardsList");
  if (!container) return;

  if (state.recommendations.length === 0) {
    container.innerHTML = `
      <div style="text-align: center; padding: 60px 20px; color: var(--text-dim); background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="width: 48px; height: 48px; margin-bottom: 12px; color: var(--primary);">
          <circle cx="12" cy="12" r="10"></circle>
          <line x1="8" y1="12" x2="16" y2="12"></line>
        </svg>
        <h4 style="color: var(--text-main); font-weight: 700; margin-bottom: 6px;">No Matching Opportunities Found</h4>
        <p style="font-size: 0.9rem; max-width: 420px; margin: 0 auto 16px auto;">
          Try adjusting your domain filter, lowering your minimum fit threshold, or adding more technical competencies above.
        </p>
      </div>
    `;
    return;
  }

  container.innerHTML = "";
  state.recommendations.forEach(rec => {
    const job = rec.internship;
    const card = document.createElement("div");
    card.className = "rec-card";

    const matchedPills = rec.matched_skills.map(s => 
      `<span class="matched-pill" title="Required Skill Matched">✓ ${s}</span>`
    ).join("");

    const missingPills = rec.missing_skills.slice(0, 3).map(s => 
      `<span class="missing-pill" title="Opportunity to Upskill">⚡ ${s}</span>`
    ).join("");

    card.innerHTML = `
      <div class="rec-card-header">
        <div class="company-logo-badge" style="background-color: ${job.company_color};">
          ${job.company_initials}
        </div>
        <div class="rec-card-meta">
          <h3 class="rec-card-title">${job.title}</h3>
          <div class="rec-card-sub">${job.company} • ${job.location} • <span style="color: #34D399; font-weight: 700;">${job.stipend}</span></div>
        </div>
        <div class="score-badge-wrap">
          <div class="score-num" style="color: ${rec.tier_color};">${Math.round(rec.match_score)}%</div>
          <div class="score-label" style="color: ${rec.tier_color};">${rec.tier_badge}</div>
        </div>
      </div>

      <div class="rec-card-desc">${job.description}</div>

      <div class="skills-match-breakdown">
        ${matchedPills}
        ${missingPills}
      </div>

      <div class="rec-card-footer">
        <button class="btn-gap-analyze" data-id="${job.id}">
          🎯 Inspect Skill Gap
        </button>
        <div style="display: flex; gap: 8px;">
          <button class="btn-secondary btn-view-job" data-id="${job.id}">
            View Details
          </button>
          <button class="btn-primary btn-apply-direct" data-id="${job.id}" data-score="${Math.round(rec.match_score)}">
            ⚡ Apply
          </button>
        </div>
      </div>
    `;

    // Event Listeners
    card.querySelector(".btn-gap-analyze")?.addEventListener("click", () => {
      loadJobIntoGapStudio(job);
      switchTab("gap-studio");
    });

    card.querySelector(".btn-view-job")?.addEventListener("click", () => {
      openJobModal(job, rec);
    });

    card.querySelector(".btn-apply-direct")?.addEventListener("click", () => {
      openApplyModal(job.id, Math.round(rec.match_score));
    });

    container.appendChild(card);
  });
}

// Setup Filters
function setupFilters() {
  // Domain pills
  const pills = document.querySelectorAll(".filter-pill");
  pills.forEach(pill => {
    pill.addEventListener("click", async () => {
      pills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      state.activeDomain = pill.getAttribute("data-domain");
      await fetchRecommendations();
    });
  });

  // Work type selector
  const workTypeSelect = document.getElementById("workTypeSelect");
  workTypeSelect?.addEventListener("change", async (e) => {
    state.activeWorkType = e.target.value;
    await fetchRecommendations();
  });

  // Match slider
  const slider = document.getElementById("minMatchSlider");
  const sliderVal = document.getElementById("sliderValueDisplay");
  slider?.addEventListener("input", async (e) => {
    state.minMatchScore = parseFloat(e.target.value);
    if (sliderVal) sliderVal.textContent = `${state.minMatchScore}%`;
  });
  slider?.addEventListener("change", async () => {
    await fetchRecommendations();
  });
}

// Load All Internships for Directory View
async function loadAllInternships() {
  try {
    const res = await fetch(`${API_BASE}/api/internships`);
    const data = await res.json();
    state.allInternships = data.internships || [];
    renderDirectory(state.allInternships);

    // Populate Gap Studio Internship Dropdown
    const gapSelect = document.getElementById("gapJobSelect");
    if (gapSelect) {
      gapSelect.innerHTML = "";
      state.allInternships.forEach(j => {
        gapSelect.innerHTML += `<option value="${j.id}">${j.company} — ${j.title}</option>`;
      });

      gapSelect.addEventListener("change", (e) => {
        const job = state.allInternships.find(j => j.id === e.target.value);
        if (job) loadJobIntoGapStudio(job);
      });
    }

    // Populate Recruiter Role Select
    const recSelect = document.getElementById("recruiterRoleSelect");
    if (recSelect) {
      recSelect.innerHTML = "";
      state.allInternships.forEach(j => {
        recSelect.innerHTML += `<option value="${j.id}">${j.company} — ${j.title}</option>`;
      });
      recSelect.addEventListener("change", (e) => {
        loadRoleApplicants(e.target.value);
      });
    }

    // Update stats banner
    const statsJobs = document.getElementById("statsJobsCount");
    if (statsJobs) statsJobs.textContent = state.allInternships.length;
  } catch (err) {
    console.error("Error loading internships:", err);
  }
}

// Render All Internships Directory
function renderDirectory(internships) {
  const grid = document.getElementById("directoryGrid");
  const searchInput = document.getElementById("dirSearchInput");

  if (!grid) return;

  const render = (list) => {
    grid.innerHTML = "";
    list.forEach(job => {
      const card = document.createElement("div");
      card.className = "dir-card";
      card.innerHTML = `
        <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
          <div class="company-logo-badge" style="background-color: ${job.company_color};">
            ${job.company_initials}
          </div>
          <div>
            <h4 style="font-size: 1.1rem; font-weight: 800; color: var(--text-main);">${job.title}</h4>
            <div style="color: var(--text-muted); font-size: 0.85rem;">${job.company} • ${job.location}</div>
          </div>
        </div>

        <div style="display: flex; gap: 8px; margin-bottom: 12px; flex-wrap: wrap;">
          <span class="matched-pill" style="background: rgba(99, 102, 241, 0.12); color: #A5B4FC; border-color: rgba(99, 102, 241, 0.3);">${job.domain}</span>
          <span class="matched-pill" style="background: rgba(16, 185, 129, 0.12); color: #6EE7B7; border-color: rgba(16, 185, 129, 0.3);">${job.work_type}</span>
          <span class="matched-pill" style="background: rgba(245, 158, 11, 0.12); color: #FCD34D; border-color: rgba(245, 158, 11, 0.3);">${job.stipend}</span>
        </div>

        <p style="font-size: 0.88rem; color: #CBD5E1; line-height: 1.5; margin-bottom: 14px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">
          ${job.description}
        </p>

        <div style="display: flex; justify-content: space-between; align-items: center; border-top: 1px solid var(--border-subtle); padding-top: 12px; margin-top: auto;">
          <button class="btn-secondary btn-dir-details" data-id="${job.id}">Role Details</button>
          <button class="btn-primary btn-dir-apply" data-id="${job.id}">⚡ Apply</button>
        </div>
      `;

      card.querySelector(".btn-dir-details")?.addEventListener("click", () => {
        openJobModal(job, null);
      });

      card.querySelector(".btn-dir-apply")?.addEventListener("click", () => {
        openApplyModal(job.id, 85);
      });

      grid.appendChild(card);
    });
  };

  render(internships);

  searchInput?.addEventListener("input", (e) => {
    const q = e.target.value.toLowerCase();
    const filtered = internships.filter(j => 
      j.title.toLowerCase().includes(q) ||
      j.company.toLowerCase().includes(q) ||
      j.domain.toLowerCase().includes(q) ||
      j.required_skills.some(s => s.toLowerCase().includes(q))
    );
    render(filtered);
  });
}

// Skill Gap Studio & What-If Simulator
async function loadJobIntoGapStudio(job) {
  state.selectedJobForGap = job;
  state.simulatedSkillsToAdd = [];

  const select = document.getElementById("gapJobSelect");
  if (select && select.value !== job.id) select.value = job.id;

  try {
    const gapUrl = API_BASE ? `${API_BASE}/api/skill-gap` : "/api/skill-gap";
    const res = await fetch(gapUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        skills: state.profile.extracted_skills || [],
        internship_id: job.id
      })
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const gapData = await res.json();
    renderGapStudio(gapData);
  } catch (err) {
    console.error("Error loading gap analysis:", err);
    // Client-side fallback gap calculation if backend is cold/unreachable
    const studentSkillsLower = (state.profile.extracted_skills || []).map(s => s.toLowerCase());
    const reqSkills = job.required_skills || [];
    const prefSkills = job.preferred_skills || [];
    const missingReq = reqSkills.filter(s => !studentSkillsLower.includes(s.toLowerCase()));
    const missingPref = prefSkills.filter(s => !studentSkillsLower.includes(s.toLowerCase()));
    const total = reqSkills.length + prefSkills.length || 1;
    const matched = total - (missingReq.length + missingPref.length);
    const fallbackData = {
      readiness_percentage: Math.round((matched / total) * 100),
      missing_required: missingReq,
      missing_preferred: missingPref,
      learning_roadmap: missingReq.map(s => ({
        skill: s,
        week: 1,
        course: `Mastering ${s}`,
        estimated_hours: 12
      }))
    };
    renderGapStudio(fallbackData);
  }
}

function renderGapStudio(gapData) {
  const job = state.selectedJobForGap;
  document.getElementById("gapJobTitleDisplay").textContent = `${job.company} — ${job.title}`;
  document.getElementById("gapCurrentScoreDisplay").textContent = `${gapData.readiness_percentage}%`;
  document.getElementById("gapProjectedScoreDisplay").textContent = `${gapData.readiness_percentage}%`;
  document.getElementById("gapScoreDeltaDisplay").textContent = "+0%";

  // Render What-If Simulator Checkboxes
  const checkboxesGrid = document.getElementById("simCheckboxesGrid");
  checkboxesGrid.innerHTML = "";

  const allMissing = [
    ...gapData.missing_required.map(s => ({ skill: s, type: "Required" })),
    ...gapData.missing_preferred.map(s => ({ skill: s, type: "Preferred" }))
  ];

  if (allMissing.length === 0) {
    checkboxesGrid.innerHTML = `<div style="color: #34D399; font-weight: 700; grid-column: 1 / -1;">✓ You already possess all required and preferred competencies for this role!</div>`;
  } else {
    allMissing.forEach(item => {
      const pill = document.createElement("label");
      pill.className = "sim-skill-check";
      pill.innerHTML = `
        <input type="checkbox" data-skill="${item.skill}">
        <span>${item.skill}</span>
        <small style="color: ${item.type === 'Required' ? '#F43F5E' : '#F59E0B'}; font-size: 0.75rem;">(${item.type})</small>
      `;

      pill.querySelector("input").addEventListener("change", (e) => {
        if (e.target.checked) {
          state.simulatedSkillsToAdd.push(item.skill);
        } else {
          state.simulatedSkillsToAdd = state.simulatedSkillsToAdd.filter(s => s !== item.skill);
        }
        simulateWhatIfScore();
      });

      checkboxesGrid.appendChild(pill);
    });
  }

  // Render Pathways Roadmap
  const pathwaysGrid = document.getElementById("pathwaysGrid");
  pathwaysGrid.innerHTML = "";

  gapData.learning_pathways.forEach((path, idx) => {
    const card = document.createElement("div");
    card.className = "pathway-card";
    card.innerHTML = `
      <div class="pathway-step-num">MILESTONE ${idx + 1}</div>
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h4 style="font-size: 1.1rem; font-weight: 800; color: var(--text-main);">${path.skill}</h4>
        <span class="matched-pill" style="background: rgba(99, 102, 241, 0.15); color: #C7D2FE;">${path.priority_badge}</span>
      </div>

      <div style="font-size: 0.88rem; color: var(--text-muted); margin-bottom: 12px;">
        <strong>Recommended Course:</strong> ${path.resource} (${path.platform})
      </div>

      <div style="background: rgba(15, 23, 42, 0.6); padding: 10px; border-radius: var(--radius-sm); margin-bottom: 12px; font-size: 0.82rem; font-family: var(--font-mono); color: #94A3B8;">
        Duration: ${path.estimated_hours} • Level: ${path.difficulty}
      </div>

      <div style="font-size: 0.82rem; color: #E2E8F0; line-height: 1.5;">
        <strong>Hands-on Project:</strong> ${path.recommended_project}
      </div>
    `;
    pathwaysGrid.appendChild(card);
  });
}

// Simulate What-If Score API Call
async function simulateWhatIfScore() {
  if (!state.selectedJobForGap) return;

  try {
    const res = await fetch(`${API_BASE}/api/simulate`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        current_skills: state.profile.extracted_skills,
        skills_to_add: state.simulatedSkillsToAdd,
        internship_id: state.selectedJobForGap.id
      })
    });
    if (!res.ok) throw new Error("Simulation failed");
    const simData = await res.json();

    document.getElementById("gapProjectedScoreDisplay").textContent = `${Math.round(simData.projected_score)}%`;
    const deltaElem = document.getElementById("gapScoreDeltaDisplay");
    deltaElem.textContent = simData.score_delta > 0 ? `+${simData.score_delta}%` : `${simData.score_delta}%`;

    if (simData.score_delta > 0) {
      showToast(simData.impact_message, "success");
    }
  } catch (err) {
    console.error("Simulation error:", err);
  }
}

// Market Trends View
async function fetchMarketTrends() {
  try {
    const res = await fetch(`${API_BASE}/api/market-trends`);
    const data = await res.json();

    // Render bars
    const barsContainer = document.getElementById("trendBarsList");
    if (barsContainer) {
      barsContainer.innerHTML = "";
      const maxScore = data.top_demanded_skills[0]?.demand_score || 1;

      data.top_demanded_skills.forEach(item => {
        const pct = (item.demand_score / maxScore) * 100;
        const row = document.createElement("div");
        row.className = "trend-bar-row";
        row.innerHTML = `
          <div class="trend-bar-meta">
            <span>${item.skill} <small style="color: var(--text-dim);">(${item.category})</small></span>
            <span style="font-family: var(--font-mono); color: #A5B4FC;">${item.demand_score} pts</span>
          </div>
          <div class="trend-bar-track">
            <div class="trend-bar-fill" style="width: ${pct}%;"></div>
          </div>
        `;
        barsContainer.appendChild(row);
      });
    }

    // Domain list
    const domainsContainer = document.getElementById("domainListContainer");
    if (domainsContainer) {
      domainsContainer.innerHTML = "";
      Object.entries(data.domain_distribution).forEach(([dom, count]) => {
        const pill = document.createElement("div");
        pill.className = "sim-skill-check";
        pill.innerHTML = `
          <div style="flex: 1;">
            <div style="font-weight: 700; color: #F8FAFC;">${dom}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">${count} Internship Openings Indexed</div>
          </div>
          <span style="font-size: 1.1rem; font-weight: 800; color: var(--primary); font-family: var(--font-mono);">${count}</span>
        `;
        domainsContainer.appendChild(pill);
      });
    }
  } catch (err) {
    console.error("Error fetching market trends:", err);
  }
}

// -------------------------------------------------------------
// Real Application Flow
// -------------------------------------------------------------
function setupApplyFlow() {
  const form = document.getElementById("applyForm");
  const cancelBtn = document.getElementById("cancelApplyBtn");

  cancelBtn?.addEventListener("click", () => {
    document.getElementById("applyModal")?.classList.remove("open");
  });

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!state.activeApplyingJob) return;

    const applicantName = document.getElementById("applyApplicantName")?.value;
    const applicantEmail = document.getElementById("applyApplicantEmail")?.value;
    const applicantEducation = document.getElementById("applyApplicantEducation")?.value;

    const payload = {
      internship_id: state.activeApplyingJob.id,
      student_id: state.profile.id || "candidate-live",
      student_name: applicantName,
      student_email: applicantEmail,
      student_education: applicantEducation,
      student_skills: state.profile.extracted_skills,
      match_score: state.activeApplyingJob.match_score || 85.0
    };

    try {
      showToast("Submitting your application...", "info");
      const res = await fetch(`${API_BASE}/api/apply`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      const data = await res.json();

      if (data.status === "already_applied") {
        showToast("You have already submitted an application for this role.", "info");
      } else {
        showToast(`Application successfully submitted to ${state.activeApplyingJob.company}!`, "success");
      }

      document.getElementById("applyModal")?.classList.remove("open");
      document.getElementById("jobModal")?.classList.remove("open");

      // If user is on applications tab, reload applications
      if (state.activeTab === "my-applications") {
        await loadMyApplications();
      }
    } catch (err) {
      console.error("Application submission error:", err);
      showToast("Failed to submit application. Please verify backend connection.", "error");
    }
  });
}

function openApplyModal(jobId, matchScore = 85) {
  const job = state.allInternships.find(j => j.id === jobId) || 
              state.recommendations.find(r => r.internship.id === jobId)?.internship;
  if (!job) return;

  state.activeApplyingJob = { ...job, match_score: matchScore };

  const label = document.getElementById("applyTargetRoleLabel");
  const nameInput = document.getElementById("applyApplicantName");
  const emailInput = document.getElementById("applyApplicantEmail");
  const eduInput = document.getElementById("applyApplicantEducation");
  const preview = document.getElementById("applyMatchScorePreview");

  if (label) label.textContent = `Applying to: ${job.title} at ${job.company}`;
  if (nameInput) nameInput.value = state.profile.name || "";
  if (emailInput) emailInput.value = state.profile.email || "";
  if (eduInput) eduInput.value = state.profile.education || "";
  if (preview) preview.innerHTML = `Calculated AI Fit Score: <strong style="color: #34D399;">${matchScore}%</strong>`;

  const modal = document.getElementById("applyModal");
  modal?.classList.add("open");
}

// -------------------------------------------------------------
// My Applications Tab
// -------------------------------------------------------------
async function loadMyApplications() {
  const container = document.getElementById("applicationsList");
  if (!container) return;

  container.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 40px;">Loading your applications...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/applications`);
    const data = await res.json();
    state.myApplications = data.applications || [];

    // Update counts
    const totalCount = state.myApplications.length;
    const underReview = state.myApplications.filter(a => a.status === "Under Review").length;
    const shortlisted = state.myApplications.filter(a => a.status === "Shortlisted" || a.status === "Interviewing").length;

    document.getElementById("totalAppsCount").textContent = totalCount;
    document.getElementById("underReviewCount").textContent = underReview;
    document.getElementById("shortlistedCount").textContent = shortlisted;

    if (state.myApplications.length === 0) {
      container.innerHTML = `
        <div style="text-align: center; padding: 60px 20px; background: var(--bg-card); border-radius: var(--radius-lg); border: 1px dashed var(--border-subtle);">
          <h4 style="color: var(--text-main); font-weight: 700; margin-bottom: 6px;">No Applications Submitted Yet</h4>
          <p style="font-size: 0.9rem; color: var(--text-muted); max-width: 440px; margin: 0 auto 16px auto;">
            Explore high-affinity matches in the Match Studio or All Internships directory and apply with one click.
          </p>
          <button class="btn-primary" onclick="switchTab('match-studio')">Explore Recommendations</button>
        </div>
      `;
      return;
    }

    container.innerHTML = "";
    state.myApplications.forEach(app => {
      const card = document.createElement("div");
      card.className = "app-card";

      let statusClass = "status-under-review";
      if (app.status === "Shortlisted") statusClass = "status-shortlisted";
      else if (app.status === "Interviewing") statusClass = "status-interviewing";
      else if (app.status === "Offered") statusClass = "status-offered";
      else if (app.status === "Rejected") statusClass = "status-rejected";

      card.innerHTML = `
        <div class="app-card-left">
          <div class="company-logo-badge" style="background-color: #6366F1;">
            ${(app.company || "CO").substring(0, 2).toUpperCase()}
          </div>
          <div>
            <div class="app-card-title">${app.internship_title}</div>
            <div class="app-card-meta">${app.company} • Applied on ${app.applied_at || "Recent"}</div>
          </div>
        </div>

        <div class="app-card-right">
          <div style="font-family: var(--font-mono); font-size: 0.95rem; font-weight: 700; color: #34D399;">
            ${Math.round(app.match_score || 85)}% Fit
          </div>
          <span class="status-badge ${statusClass}">${app.status}</span>
        </div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading applications:", err);
    container.innerHTML = `<div style="text-align: center; color: #F87171; padding: 40px;">Failed to load applications.</div>`;
  }
}

// -------------------------------------------------------------
// Recruiter Hub Tab & Workflows
// -------------------------------------------------------------
async function loadRecruiterHub() {
  if (state.allInternships.length > 0) {
    const defaultJobId = state.allInternships[0].id;
    const select = document.getElementById("recruiterRoleSelect");
    if (select && !select.value) select.value = defaultJobId;
    await loadRoleApplicants(select?.value || defaultJobId);
  }
  await loadCandidatePool();
}

async function loadRoleApplicants(internshipId) {
  const container = document.getElementById("applicantsPipelineList");
  if (!container) return;

  container.innerHTML = `<div style="text-align: center; color: var(--text-dim); padding: 30px;">Calculating AI applicant matches...</div>`;

  try {
    const res = await fetch(`${API_BASE}/api/recruiter/internships/${internshipId}/applicants`);
    const data = await res.json();
    const applicants = data.applicants || [];

    if (applicants.length === 0) {
      container.innerHTML = `<div style="color: var(--text-dim); text-align: center; padding: 30px;">No applicants found for this role yet.</div>`;
      return;
    }

    container.innerHTML = "";
    applicants.forEach(cand => {
      const card = document.createElement("div");
      card.className = "applicant-card";

      const skillsHtml = (cand.extracted_skills || []).slice(0, 4).map(s => 
        `<span class="matched-pill" style="font-size: 0.72rem; padding: 2px 7px;">${s}</span>`
      ).join("");

      card.innerHTML = `
        <div class="applicant-card-header">
          <div>
            <div class="applicant-name">${cand.name}</div>
            <div class="applicant-meta">${cand.education || cand.email || "Candidate"}</div>
          </div>
          <div class="applicant-score">${Math.round(cand.match_score)}% Fit</div>
        </div>

        <div class="applicant-skills-pills">${skillsHtml}</div>

        <div class="applicant-actions-bar">
          <span style="font-size: 0.75rem; color: var(--text-dim);">Application Status:</span>
          ${cand.application_id ? `
            <select class="select-custom status-change-select" style="padding: 4px 10px; font-size: 0.75rem;" data-appid="${cand.application_id}">
              <option value="Under Review" ${cand.application_status === 'Under Review' ? 'selected' : ''}>Under Review</option>
              <option value="Shortlisted" ${cand.application_status === 'Shortlisted' ? 'selected' : ''}>Shortlisted</option>
              <option value="Interviewing" ${cand.application_status === 'Interviewing' ? 'selected' : ''}>Interviewing</option>
              <option value="Offered" ${cand.application_status === 'Offered' ? 'selected' : ''}>Offered</option>
              <option value="Rejected" ${cand.application_status === 'Rejected' ? 'selected' : ''}>Rejected</option>
            </select>
          ` : `
            <span class="matched-pill" style="background: rgba(99, 102, 241, 0.15); color: #A5B4FC; font-size: 0.75rem;">Pool Scout</span>
          `}
        </div>
      `;

      card.querySelector(".status-change-select")?.addEventListener("change", async (e) => {
        const appId = e.target.getAttribute("data-appid");
        const newStatus = e.target.value;
        await updateApplicantStatus(appId, newStatus);
      });

      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading role applicants:", err);
    container.innerHTML = `<div style="color: #F87171; text-align: center; padding: 30px;">Failed to load applicants.</div>`;
  }
}

async function updateApplicantStatus(appId, status) {
  try {
    const res = await fetch(`${API_BASE}/api/applications/${appId}/status`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ status })
    });
    if (!res.ok) throw new Error("Status update failed");
    showToast(`Applicant status updated to '${status}'`, "success");
  } catch (err) {
    console.error("Status update error:", err);
    showToast("Failed to update status", "error");
  }
}

async function loadCandidatePool() {
  const container = document.getElementById("candidatePoolList");
  const countBadge = document.getElementById("scoutPoolCount");
  if (!container) return;

  try {
    const res = await fetch(`${API_BASE}/api/candidates`);
    const data = await res.json();
    const candidates = data.candidates || [];

    if (countBadge) countBadge.textContent = `${candidates.length} Candidates`;

    container.innerHTML = "";
    candidates.forEach(c => {
      const card = document.createElement("div");
      card.className = "candidate-scout-card";
      const skills = (c.extracted_skills || []).slice(0, 5).map(s => 
        `<span class="matched-pill" style="font-size: 0.72rem; padding: 2px 7px;">${s}</span>`
      ).join("");

      card.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <div style="font-weight: 800; color: var(--text-main); font-size: 0.95rem;">${c.name}</div>
          <span style="font-size: 0.75rem; color: #34D399; font-weight: 700;">Verified Talent</span>
        </div>
        <div style="font-size: 0.8rem; color: var(--text-muted);">${c.education || c.email}</div>
        <div style="display: flex; flex-wrap: wrap; gap: 4px; margin-top: 4px;">${skills}</div>
      `;
      container.appendChild(card);
    });
  } catch (err) {
    console.error("Error loading candidate pool:", err);
  }
}

// -------------------------------------------------------------
// Post Job Flow
// -------------------------------------------------------------
function setupPostJobFlow() {
  const modal = document.getElementById("postJobModal");
  const openBtn1 = document.getElementById("headerPostJobBtn");
  const openBtn2 = document.getElementById("openPostJobModalBtn");
  const closeBtn = document.getElementById("postJobModalCloseBtn");
  const cancelBtn = document.getElementById("cancelPostJobBtn");
  const form = document.getElementById("postJobForm");

  const openModal = () => modal?.classList.add("open");
  const closeModal = () => modal?.classList.remove("open");

  openBtn1?.addEventListener("click", openModal);
  openBtn2?.addEventListener("click", openModal);
  closeBtn?.addEventListener("click", closeModal);
  cancelBtn?.addEventListener("click", closeModal);

  form?.addEventListener("submit", async (e) => {
    e.preventDefault();
    const title = document.getElementById("postJobTitle")?.value;
    const company = document.getElementById("postJobCompany")?.value;
    const domain = document.getElementById("postJobDomain")?.value;
    const workType = document.getElementById("postJobWorkType")?.value;
    const location = document.getElementById("postJobLocation")?.value || "Remote";
    const stipend = document.getElementById("postJobStipend")?.value || "$50/hr";
    const reqStr = document.getElementById("postJobReqSkills")?.value || "";
    const prefStr = document.getElementById("postJobPrefSkills")?.value || "";
    const desc = document.getElementById("postJobDescription")?.value;

    const payload = {
      title,
      company,
      domain,
      work_type: workType,
      location,
      stipend,
      duration: "12 Weeks (Summer 2026)",
      level: "Undergrad / Masters",
      description: desc,
      required_skills: reqStr.split(",").map(s => s.trim()).filter(Boolean),
      preferred_skills: prefStr.split(",").map(s => s.trim()).filter(Boolean),
      responsibilities: [
        `Contribute to core ${domain} production deliverables`,
        "Collaborate cross-functionally with senior mentors and peers"
      ],
      learning_outcomes: [
        "Hands-on engineering experience with industry best practices",
        "Direct mentorship from senior technical leads"
      ]
    };

    try {
      showToast("Publishing internship opening...", "info");
      const res = await fetch(`${API_BASE}/api/internships`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });
      if (!res.ok) throw new Error("Failed to post internship");
      const data = await res.json();

      showToast(`Internship '${title}' published & indexed!`, "success");
      closeModal();
      form.reset();

      // Refresh internships directory
      await loadAllInternships();
      await fetchRecommendations();
    } catch (err) {
      console.error("Job posting error:", err);
      showToast("Failed to post opening.", "error");
    }
  });
}

// -------------------------------------------------------------
// Profile Editor
// -------------------------------------------------------------
function setupProfileEditor() {
  const modal = document.getElementById("profileEditModal");
  const editBtn = document.getElementById("editProfileBtn");
  const headerBadge = document.getElementById("headerUserBadge");
  const closeBtn = document.getElementById("profileEditModalCloseBtn");
  const cancelBtn = document.getElementById("cancelProfileEditBtn");
  const form = document.getElementById("profileEditForm");

  const openModal = () => {
    document.getElementById("editProfileName").value = state.profile.name || "";
    document.getElementById("editProfileEmail").value = state.profile.email || "";
    document.getElementById("editProfileEducation").value = state.profile.education || "";
    document.getElementById("editProfileGithub").value = state.profile.links?.github || "";
    document.getElementById("editProfileLinkedin").value = state.profile.links?.linkedin || "";
    modal?.classList.add("open");
  };

  const closeModal = () => modal?.classList.remove("open");

  editBtn?.addEventListener("click", openModal);
  headerBadge?.addEventListener("click", openModal);
  closeBtn?.addEventListener("click", closeModal);
  cancelBtn?.addEventListener("click", closeModal);

  form?.addEventListener("submit", (e) => {
    e.preventDefault();
    state.profile.name = document.getElementById("editProfileName").value.trim();
    state.profile.email = document.getElementById("editProfileEmail").value.trim();
    state.profile.education = document.getElementById("editProfileEducation").value.trim();
    state.profile.links = state.profile.links || {};
    state.profile.links.github = document.getElementById("editProfileGithub").value.trim();
    state.profile.links.linkedin = document.getElementById("editProfileLinkedin").value.trim();

    updateCandidateProfile(state.profile, true);
    closeModal();
    showToast("Candidate profile updated successfully!", "success");
  });
}

// -------------------------------------------------------------
// Modal Management
// -------------------------------------------------------------
function setupModals() {
  const jobModal = document.getElementById("jobModal");
  const jobClose = document.getElementById("modalCloseBtn");
  jobClose?.addEventListener("click", () => jobModal?.classList.remove("open"));
  jobModal?.addEventListener("click", (e) => {
    if (e.target === jobModal) jobModal.classList.remove("open");
  });

  const applyModal = document.getElementById("applyModal");
  const applyClose = document.getElementById("applyModalCloseBtn");
  applyClose?.addEventListener("click", () => applyModal?.classList.remove("open"));

  const profileModal = document.getElementById("profileEditModal");
  profileModal?.addEventListener("click", (e) => {
    if (e.target === profileModal) profileModal.classList.remove("open");
  });

  const postJobModal = document.getElementById("postJobModal");
  postJobModal?.addEventListener("click", (e) => {
    if (e.target === postJobModal) postJobModal.classList.remove("open");
  });
}

function openJobModal(job, rec) {
  const modal = document.getElementById("jobModal");
  const modalBody = document.getElementById("modalBody");
  if (!modal || !modalBody) return;

  const score = rec ? Math.round(rec.match_score) : 85;

  modalBody.innerHTML = `
    <div style="display: flex; align-items: center; gap: 14px; margin-bottom: 20px;">
      <div class="company-logo-badge" style="background-color: ${job.company_color}; width: 56px; height: 56px; font-size: 1.4rem;">
        ${job.company_initials}
      </div>
      <div>
        <h3 style="font-size: 1.4rem; font-weight: 800; color: var(--text-main);">${job.title}</h3>
        <p style="color: var(--text-muted); font-size: 0.9rem;">${job.company} • ${job.location} • <span style="color: #34D399; font-weight: 700;">${job.stipend}</span></p>
      </div>
    </div>

    ${rec ? `
      <div style="background: rgba(99, 102, 241, 0.12); border: 1px solid rgba(99, 102, 241, 0.3); border-radius: 12px; padding: 14px; margin-bottom: 20px; display: flex; justify-content: space-between; align-items: center;">
        <div>
          <span style="font-size: 0.8rem; text-transform: uppercase; color: var(--text-dim); font-weight: 700;">Match Fit Evaluation</span>
          <h4 style="font-size: 1.2rem; font-weight: 800; color: ${rec.tier_color};">${rec.tier_badge} (${Math.round(rec.match_score)}% Score)</h4>
        </div>
        <div style="text-align: right; font-size: 0.82rem; font-family: var(--font-mono); color: #C7D2FE;">
          Skill Match: ${rec.score_breakdown.skill_overlap}%<br>
          Semantic: ${rec.score_breakdown.semantic_similarity}%
        </div>
      </div>
    ` : ''}

    <div style="margin-bottom: 18px;">
      <h5 style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; color: var(--text-dim); margin-bottom: 6px;">Role Overview:</h5>
      <p style="color: #E2E8F0; font-size: 0.92rem; line-height: 1.6;">${job.description}</p>
    </div>

    <div style="margin-bottom: 18px;">
      <h5 style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Key Responsibilities:</h5>
      <ul style="color: var(--text-muted); font-size: 0.88rem; padding-left: 20px; line-height: 1.7;">
        ${job.responsibilities.map(r => `<li>${r}</li>`).join("")}
      </ul>
    </div>

    <div style="margin-bottom: 18px;">
      <h5 style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Required Competencies:</h5>
      <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        ${job.required_skills.map(s => `<span class="matched-pill" style="background: rgba(99, 102, 241, 0.15); color: #C7D2FE; border-color: rgba(99, 102, 241, 0.3);">${s}</span>`).join("")}
      </div>
    </div>

    <div style="margin-bottom: 24px;">
      <h5 style="font-size: 0.85rem; font-weight: 800; text-transform: uppercase; color: var(--text-dim); margin-bottom: 8px;">Preferred Skills:</h5>
      <div style="display: flex; flex-wrap: wrap; gap: 6px;">
        ${job.preferred_skills.map(s => `<span class="matched-pill" style="background: rgba(245, 158, 11, 0.12); color: #FCD34D; border-color: rgba(245, 158, 11, 0.3);">${s}</span>`).join("")}
      </div>
    </div>

    <div style="display: flex; justify-content: flex-end; gap: 12px; border-top: 1px solid var(--border-subtle); padding-top: 18px;">
      <button class="btn-secondary" onclick="document.getElementById('jobModal').classList.remove('open')">Close</button>
      <button class="btn-primary" onclick="openApplyModal('${job.id}', ${score})">
        ⚡ Apply for Internship
      </button>
    </div>
  `;

  modal.classList.add("open");
}
