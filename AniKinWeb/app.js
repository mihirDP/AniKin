document.addEventListener('DOMContentLoaded', () => {
    initViewSwitching();
    initModuleTabs();
    initViewportSimulator();
    initDocsSystem();
});

/* 1. View Switching (Home vs Docs) */
function initViewSwitching() {
    const homeView = document.getElementById('home-view');
    const docsView = document.getElementById('docs-view');
    const navDocsLink = document.getElementById('nav-docs-link');
    const footerDocsLink = document.querySelector('.docs-toggle-footer');
    const logo = document.querySelector('.logo');
    const otherNavLinks = document.querySelectorAll('.nav-links a:not(#nav-docs-link)');

    function showDocs(e) {
        if (e) e.preventDefault();
        homeView.classList.add('hidden');
        docsView.classList.remove('hidden');
        navDocsLink.classList.add('active');
        otherNavLinks.forEach(link => link.classList.remove('active'));
        window.scrollTo(0, 0);
    }

    function showHome(e, targetHash) {
        docsView.classList.add('hidden');
        homeView.classList.remove('hidden');
        navDocsLink.classList.remove('active');
        
        if (targetHash) {
            const targetEl = document.querySelector(targetHash);
            if (targetEl) {
                setTimeout(() => {
                    targetEl.scrollIntoView({ behavior: 'smooth' });
                }, 50);
            }
        } else {
            window.scrollTo(0, 0);
        }
    }

    navDocsLink.addEventListener('click', showDocs);
    if (footerDocsLink) footerDocsLink.addEventListener('click', showDocs);

    logo.addEventListener('click', (e) => {
        e.preventDefault();
        showHome(e, null);
    });

    otherNavLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            const hash = link.getAttribute('href');
            if (hash.startsWith('#')) {
                e.preventDefault();
                showHome(e, hash);
            }
        });
    });

    // Check URL hash on load
    if (window.location.hash === '#docs') {
        showDocs();
    }
}

/* 2. Features Section Modules Tabs */
function initModuleTabs() {
    const tabs = document.querySelectorAll('.module-tab');
    const details = document.querySelectorAll('.module-detail');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            details.forEach(d => d.classList.remove('active'));

            tab.classList.add('active');
            const targetId = tab.getAttribute('data-target');
            document.getElementById(targetId).classList.add('active');
        });
    });
}

/* 3. Interactive Viewport Simulator */
function initViewportSimulator() {
    const bone1 = document.querySelector('.bone-1');
    const bone2 = document.querySelector('.bone-2');
    const targetNode = document.querySelector('.target-node');
    const tweenSlider = document.getElementById('demo-tween-slider');
    const easeSlider = document.getElementById('demo-ease-slider');
    const trailBtn = document.getElementById('demo-trail-btn');
    const ghostBtn = document.getElementById('demo-ghost-btn');
    const trailContainer = document.querySelector('.svg-trail-container');
    const ghostRigs = document.querySelectorAll('.ghost-rig');

    // Bone lengths
    const l1 = 100;
    const l2 = 80;

    // Define prev pose angles (0% key) and next pose angles (100% key)
    const prevPose = { theta1: -45, theta2: 60 };
    const nextPose = { theta1: 15, theta2: -30 };

    // Function to calculate forward kinematics to place the target node
    function updateBones(theta1, theta2) {
        // Apply rotation to bone 1 (relative to parent joint at 0, 100 in container)
        bone1.style.transform = `rotate(${theta1}deg)`;

        // Calculate end of bone 1 in container space
        const rad1 = (theta1 * Math.PI) / 180;
        const x1 = l1 * Math.cos(rad1);
        const y1 = l1 * Math.sin(rad1) + 100;

        // Position bone 2 at the end of bone 1
        bone2.style.left = `${x1}px`;
        bone2.style.top = `${y1}px`;
        bone2.style.transform = `rotate(${theta1 + theta2}deg)`;

        // Calculate end of bone 2 (Target Node position)
        const rad2 = ((theta1 + theta2) * Math.PI) / 180;
        const x2 = x1 + l2 * Math.cos(rad2);
        const y2 = y1 + l2 * Math.sin(rad2);

        targetNode.style.left = `${x2 - 6}px`; // center the 12px dot
        targetNode.style.top = `${y2 - 6}px`;
    }

    // Easing helper (cubic ease-in-out)
    function easeInOutCubic(t) {
        return t < 0.5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    }

    // Apply interpolation
    function applyInterpolation(t, isEased = false) {
        const factor = isEased ? easeInOutCubic(t) : t;
        const theta1 = prevPose.theta1 + (nextPose.theta1 - prevPose.theta1) * factor;
        const theta2 = prevPose.theta2 + (nextPose.theta2 - prevPose.theta2) * factor;
        updateBones(theta1, theta2);
    }

    // Initial setup
    updateBones(prevPose.theta1, prevPose.theta2);

    // Slider inputs
    tweenSlider.addEventListener('input', (e) => {
        const t = e.target.value / 100;
        applyInterpolation(t, false);
        easeSlider.value = e.target.value; // Keep sync visually
    });

    easeSlider.addEventListener('input', (e) => {
        const t = e.target.value / 100;
        applyInterpolation(t, true);
        tweenSlider.value = e.target.value; // Keep sync visually
    });

    // Reset sliders on release (snaps back to 50%)
    tweenSlider.addEventListener('change', () => {
        animateToMidpoint();
    });
    easeSlider.addEventListener('change', () => {
        animateToMidpoint();
    });

    function animateToMidpoint() {
        const startVal = parseInt(tweenSlider.value);
        const endVal = 50;
        const duration = 200; // ms
        const startTime = performance.now();

        function step(now) {
            const elapsed = now - startTime;
            const progress = Math.min(elapsed / duration, 1);
            const currentVal = startVal + (endVal - startVal) * progress;
            
            tweenSlider.value = currentVal;
            easeSlider.value = currentVal;
            applyInterpolation(currentVal / 100, false);

            if (progress < 1) {
                requestAnimationFrame(step);
            }
        }
        requestAnimationFrame(step);
    }

    // Toggle Trail
    trailBtn.addEventListener('click', () => {
        trailBtn.classList.toggle('active');
        trailContainer.classList.toggle('active');
    });

    // Toggle Ghosting
    ghostBtn.addEventListener('click', () => {
        ghostBtn.classList.toggle('active');
        ghostRigs.forEach(rig => rig.classList.toggle('active'));
    });
}

/* 4. Searchable Documentation System */
function initDocsSystem() {
    const searchInput = document.getElementById('docs-search-input');
    const docLinks = document.querySelectorAll('.docs-nav-link');
    const docPages = document.querySelectorAll('.doc-page');

    // Tab switcher inside Docs
    docLinks.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetDoc = link.getAttribute('data-doc');
            
            docLinks.forEach(l => l.classList.remove('active'));
            docPages.forEach(p => p.classList.remove('active'));

            link.classList.add('active');
            document.getElementById(targetDoc).classList.add('active');
            window.scrollTo(0, 0);
        });
    });

    // Search Filtering
    searchInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        
        docLinks.forEach(link => {
            const docId = link.getAttribute('data-doc');
            const pageEl = document.getElementById(docId);
            const pageText = pageEl.textContent.toLowerCase();
            const linkText = link.textContent.toLowerCase();

            // Match query in link text OR page body text
            if (query === '' || pageText.includes(query) || linkText.includes(query)) {
                link.style.display = 'block';
            } else {
                link.style.display = 'none';
            }
        });
    });
}
