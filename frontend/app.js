/**
 * SnapCartAI — Frontend Logic
 * Handles URL submission, pipeline progress, and result rendering
 */

const API_BASE = window.location.origin;

// ── Category Emoji Map ──────────────────────────────────────────
const CATEGORY_EMOJIS = {
    produce: "🥬",
    dairy: "🥛",
    meat: "🥩",
    spices: "🌶️",
    pantry: "🫙",
    frozen: "🧊",
    other: "🧺",
    grain: "🌾",
    oil: "🫒",
    sauce: "🥫",
    default: "🛒",
};

function getCategoryEmoji(category) {
    if (!category) return CATEGORY_EMOJIS.default;
    const lower = category.toLowerCase();
    return CATEGORY_EMOJIS[lower] || CATEGORY_EMOJIS.default;
}

// ── Pipeline Step Management ────────────────────────────────────
const STEPS = ["url", "audio", "transcribe", "ingredients", "cart"];

function resetPipeline() {
    STEPS.forEach((step) => {
        const el = document.getElementById(`step-${step}`);
        el.className = "step";
        document.getElementById(`step-${step}-status`).textContent = "Waiting...";
    });
}

function setStepActive(step, statusText) {
    const el = document.getElementById(`step-${step}`);
    el.className = "step active";
    document.getElementById(`step-${step}-status`).textContent = statusText || "Processing...";
}

function setStepCompleted(step, statusText) {
    const el = document.getElementById(`step-${step}`);
    el.className = "step completed";
    document.getElementById(`step-${step}-status`).textContent = statusText || "Done";
}

function setStepError(step, statusText) {
    const el = document.getElementById(`step-${step}`);
    el.className = "step error";
    document.getElementById(`step-${step}-status`).textContent = statusText || "Failed";
}

// ── Main Process Function ───────────────────────────────────────
async function processURL() {
    const input = document.getElementById("url-input");
    const btn = document.getElementById("process-btn");
    const url = input.value.trim();

    if (!url) {
        input.focus();
        input.style.borderColor = "var(--error)";
        setTimeout(() => (input.style.borderColor = ""), 2000);
        return;
    }

    // Show pipeline, hide previous results/errors
    document.getElementById("pipeline-section").style.display = "block";
    document.getElementById("results-section").style.display = "none";
    document.getElementById("error-section").style.display = "none";

    // Reset and start
    resetPipeline();
    btn.disabled = true;
    btn.querySelector(".btn-text").style.display = "none";
    btn.querySelector(".btn-loader").style.display = "inline-flex";

    // Animate steps with simulated progress
    setStepActive("url", "Parsing URL...");

    try {
        // Simulate step progress (since API is single-shot, we animate sequentially)
        const stepTimers = [
            { step: "url", delay: 500, msg: "URL validated ✓" },
            { step: "audio", delay: 1500, msg: "Downloading audio..." },
            { step: "transcribe", delay: 8000, msg: "Transcribing with Whisper..." },
            { step: "ingredients", delay: 3000, msg: "Extracting ingredients..." },
            { step: "cart", delay: 2000, msg: "Adding to cart..." },
        ];

        // Start animation sequence (runs independently of API call)
        let animationIndex = 0;
        const animationInterval = setInterval(() => {
            if (animationIndex > 0) {
                setStepCompleted(stepTimers[animationIndex - 1].step);
            }
            if (animationIndex < stepTimers.length) {
                setStepActive(
                    stepTimers[animationIndex].step,
                    stepTimers[animationIndex].msg
                );
            }
            animationIndex++;
            if (animationIndex > stepTimers.length) {
                clearInterval(animationInterval);
            }
        }, 3000);

        // Make the actual API call
        const response = await fetch(`${API_BASE}/api/process-url`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ url }),
        });

        clearInterval(animationInterval);

        if (!response.ok) {
            const errorData = await response.json();
            const errorDetail = errorData.detail;

            // Mark all steps based on what completed
            STEPS.forEach((step) => setStepCompleted(step, "—"));

            throw new Error(
                typeof errorDetail === "object"
                    ? errorDetail.message
                    : errorDetail || "Processing failed"
            );
        }

        const data = await response.json();

        // Mark all steps as completed
        STEPS.forEach((step) => setStepCompleted(step, "Done ✓"));

        // Render results
        renderResults(data);
    } catch (error) {
        showError(error.message);
    } finally {
        btn.disabled = false;
        btn.querySelector(".btn-text").style.display = "inline";
        btn.querySelector(".btn-loader").style.display = "none";
    }
}

// ── Render Results ──────────────────────────────────────────────
function renderResults(data) {
    const result = data.final_result;
    if (!result) {
        showError("No results returned from pipeline.");
        return;
    }

    // Dish Info
    document.getElementById("dish-name").textContent = result.dish_name || "Recipe Detected";
    document.getElementById("dish-cuisine").textContent = result.cuisine || "Various";
    document.getElementById("dish-servings").textContent = result.servings
        ? `${result.servings} servings`
        : "Servings N/A";
    document.getElementById("dish-notes").textContent = result.notes || "";

    // Ingredients Grid
    const grid = document.getElementById("ingredients-grid");
    grid.innerHTML = "";

    if (result.ingredients && result.ingredients.length > 0) {
        result.ingredients.forEach((ing) => {
            const item = document.createElement("div");
            item.className = "ingredient-item";
            item.innerHTML = `
                <span class="ingredient-emoji">${getCategoryEmoji(ing.category)}</span>
                <div class="ingredient-details">
                    <span class="ingredient-name" title="${ing.name}">${ing.name}</span>
                    <span class="ingredient-qty">${ing.quantity || "as needed"}</span>
                    <span class="ingredient-category">${ing.category || "other"}</span>
                </div>
            `;
            grid.appendChild(item);
        });
    }

    // Cart Summary
    const cartSummary = document.getElementById("cart-summary");
    const summary = result.cart_summary || {};
    cartSummary.innerHTML = `
        <div class="cart-stat">
            <div class="cart-stat-value">${summary.total || 0}</div>
            <div class="cart-stat-label">Total Items</div>
        </div>
        <div class="cart-stat">
            <div class="cart-stat-value">${summary.added_via_mcp || 0}</div>
            <div class="cart-stat-label">Added via MCP</div>
        </div>
        <div class="cart-stat">
            <div class="cart-stat-value">${summary.fallback_urls || 0}</div>
            <div class="cart-stat-label">Search Links</div>
        </div>
    `;

    // Cart Actions
    const cartActions = document.getElementById("cart-actions");
    cartActions.innerHTML = "";

    if (summary.combined_search_url) {
        const link = document.createElement("a");
        link.className = "cart-link";
        link.href = summary.combined_search_url;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        link.innerHTML = `
            <span class="cart-link-icon">🛒</span>
            <span>Open Swiggy Instamart — Search All Ingredients</span>
        `;
        cartActions.appendChild(link);
    }

    // Individual ingredient links
    if (result.cart_items && result.cart_items.length > 0) {
        result.cart_items.forEach((item) => {
            if (item.search_url) {
                const link = document.createElement("a");
                link.className = "cart-link";
                link.href = item.search_url;
                link.target = "_blank";
                link.rel = "noopener noreferrer";
                link.innerHTML = `
                    <span class="cart-link-icon">${getCategoryEmoji(null)}</span>
                    <span>Search: ${item.ingredient}</span>
                `;
                cartActions.appendChild(link);
            }
        });
    }

    // Timing
    const timingGrid = document.getElementById("timing-grid");
    timingGrid.innerHTML = "";
    const timing = data.timing || {};

    const timingLabels = {
        url_parsing: "URL Parsing",
        audio_extraction: "Audio Download",
        transcription: "Transcription",
        ingredient_extraction: "LLM Extraction",
        cart: "Cart Actions",
        total: "Total",
    };

    Object.entries(timing).forEach(([key, value]) => {
        const item = document.createElement("div");
        item.className = "timing-item";
        item.innerHTML = `
            <div class="timing-value">${value}s</div>
            <div class="timing-label">${timingLabels[key] || key}</div>
        `;
        timingGrid.appendChild(item);
    });

    // Show results
    document.getElementById("results-section").style.display = "flex";
    document.getElementById("results-section").scrollIntoView({ behavior: "smooth" });
}

// ── Show Error ──────────────────────────────────────────────────
function showError(message) {
    document.getElementById("error-title").textContent = "Something went wrong";
    document.getElementById("error-message").textContent = message;
    document.getElementById("error-section").style.display = "block";
    document.getElementById("results-section").style.display = "none";
}

// ── Keyboard Shortcut ───────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
    const input = document.getElementById("url-input");
    input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            processURL();
        }
    });

    // Focus input on page load
    input.focus();
});
