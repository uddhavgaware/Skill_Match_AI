/**
 * SkillMatch AI - HTML5 Canvas Radar & Visual Analytics Engine
 * High-DPI animated radar charts and progress visualizers.
 */

class RadarChart {
  constructor(canvasId) {
    this.canvas = document.getElementById(canvasId);
    if (!this.canvas) return;
    this.ctx = this.canvas.getContext('2d');
    
    // Default 6 pillars
    this.labels = ['AI & ML', 'Fullstack', 'Data & Analytics', 'Cloud & DevOps', 'Systems & CS', 'Product & Design'];
    this.currentValues = [20, 20, 20, 20, 20, 20];
    this.targetValues = [20, 20, 20, 20, 20, 20];
    this.animationProgress = 1.0;
    this.animating = false;

    this.resize();
    window.addEventListener('resize', () => this.resize());
  }

  resize() {
    if (!this.canvas) return;
    const rect = this.canvas.getBoundingClientRect();
    const dpr = window.devicePixelRatio || 1;
    this.width = rect.width || 320;
    this.height = rect.height || 260;
    
    this.canvas.width = this.width * dpr;
    this.canvas.height = this.height * dpr;
    this.ctx.scale(dpr, dpr);
    this.draw();
  }

  updatePillars(pillarDict) {
    if (!pillarDict) return;
    this.targetValues = this.labels.map(label => {
      const val = pillarDict[label];
      return typeof val === 'number' ? Math.max(10, Math.min(100, val)) : 20;
    });

    this.animateTransition();
  }

  animateTransition() {
    const startValues = [...this.currentValues];
    const duration = 600; // ms
    const startTime = performance.now();

    const step = (now) => {
      const elapsed = now - startTime;
      const progress = Math.min(1, elapsed / duration);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);

      for (let i = 0; i < this.labels.length; i++) {
        this.currentValues[i] = startValues[i] + (this.targetValues[i] - startValues[i]) * ease;
      }

      this.draw();

      if (progress < 1) {
        requestAnimationFrame(step);
      } else {
        this.currentValues = [...this.targetValues];
        this.draw();
      }
    };

    requestAnimationFrame(step);
  }

  draw() {
    if (!this.ctx) return;
    const ctx = this.ctx;
    const centerX = this.width / 2;
    const centerY = this.height / 2 + 6;
    const maxRadius = Math.min(centerX, centerY) - 38;
    const numAxes = this.labels.length;
    const angleStep = (Math.PI * 2) / numAxes;

    ctx.clearRect(0, 0, this.width, this.height);

    // 1. Draw concentric background polygon web rings (20%, 40%, 60%, 80%, 100%)
    const levels = [0.25, 0.50, 0.75, 1.0];
    levels.forEach((lvl, lvlIdx) => {
      ctx.beginPath();
      for (let i = 0; i < numAxes; i++) {
        const angle = i * angleStep - Math.PI / 2;
        const r = maxRadius * lvl;
        const x = centerX + Math.cos(angle) * r;
        const y = centerY + Math.sin(angle) * r;
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.closePath();
      ctx.strokeStyle = lvlIdx === levels.length - 1 ? 'rgba(255, 255, 255, 0.12)' : 'rgba(255, 255, 255, 0.05)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Subtle fill on innermost ring
      if (lvlIdx === 0) {
        ctx.fillStyle = 'rgba(15, 23, 42, 0.4)';
        ctx.fill();
      }
    });

    // 2. Draw axis lines
    for (let i = 0; i < numAxes; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const x = centerX + Math.cos(angle) * maxRadius;
      const y = centerY + Math.sin(angle) * maxRadius;

      ctx.beginPath();
      ctx.moveTo(centerX, centerY);
      ctx.lineTo(x, y);
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.08)';
      ctx.lineWidth = 1;
      ctx.stroke();

      // Axis Labels
      const labelDist = maxRadius + 20;
      const labelX = centerX + Math.cos(angle) * labelDist;
      const labelY = centerY + Math.sin(angle) * labelDist;

      ctx.font = '600 10px Plus Jakarta Sans, sans-serif';
      ctx.fillStyle = '#94A3B8';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const labelText = this.labels[i];
      const valText = `${Math.round(this.currentValues[i])}%`;
      ctx.fillText(labelText, labelX, labelY - 5);
      
      ctx.font = '700 9px JetBrains Mono, monospace';
      ctx.fillStyle = '#6366F1';
      ctx.fillText(valText, labelX, labelY + 7);
    }

    // 3. Draw Candidate Skill Radar Polygon
    ctx.beginPath();
    const points = [];
    for (let i = 0; i < numAxes; i++) {
      const angle = i * angleStep - Math.PI / 2;
      const normalizedVal = (this.currentValues[i] || 15) / 100;
      const r = maxRadius * normalizedVal;
      const x = centerX + Math.cos(angle) * r;
      const y = centerY + Math.sin(angle) * r;
      points.push({ x, y });
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.closePath();

    // Gradient fill
    const grad = ctx.createRadialGradient(centerX, centerY, 5, centerX, centerY, maxRadius);
    grad.addColorStop(0, 'rgba(99, 102, 241, 0.45)');
    grad.addColorStop(0.7, 'rgba(139, 92, 246, 0.25)');
    grad.addColorStop(1, 'rgba(236, 72, 153, 0.15)');
    ctx.fillStyle = grad;
    ctx.fill();

    // Glowing border stroke
    ctx.strokeStyle = '#6366F1';
    ctx.lineWidth = 2.5;
    ctx.shadowColor = 'rgba(99, 102, 241, 0.8)';
    ctx.shadowBlur = 12;
    ctx.stroke();
    ctx.shadowBlur = 0; // reset

    // 4. Draw glowing vertex dots
    points.forEach((pt, i) => {
      ctx.beginPath();
      ctx.arc(pt.x, pt.y, 4, 0, Math.PI * 2);
      ctx.fillStyle = '#FFFFFF';
      ctx.shadowColor = '#6366F1';
      ctx.shadowBlur = 8;
      ctx.fill();
      ctx.shadowBlur = 0;
      ctx.strokeStyle = '#6366F1';
      ctx.lineWidth = 2;
      ctx.stroke();
    });
  }
}

window.RadarChart = RadarChart;
