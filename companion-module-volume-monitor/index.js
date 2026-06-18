// Volume Monitor — https://github.com/Tech127x/volume-monitor
// Copyright (c) 2025 Tech127x

const {
    InstanceBase,
    runEntrypoint,
    InstanceStatus,
} = require("@companion-module/base");
const fs = require("fs");
const path = require("path");

const BUNDLED_ICON_DIR = path.resolve(__dirname, "icons");

const APP_COLORS = {
    brave: "#fb542b",
    firefox: "#ff6611",
    floorp: "#0a8cff",
    chrome: "#4285f4",
    chromium: "#4285f4",
    msedge: "#0078d7",
    vivaldi: "#ef3939",
    opera: "#ff1b2d",
    spotify: "#1db954",
    discord: "#5865f2",
    steam: "#1b2838",
    thunderbird: "#0a84ff",
    slack: "#4a154b",
    signal: "#3a76f0",
    telegram: "#26a5e4",
    whatsapp: "#25d366",
    mpv: "#ff6600",
    vlc: "#ff8c00",
    audacity: "#0033cc",
    obs: "#302e31",
    zoom: "#2d8cff",
    teams: "#6264a7",
    plex: "#e5a00d",
    youtube: "#ff0000",
    twitch: "#9146ff",
};

function parseAppName(raw) {
    if (!raw || typeof raw !== "string") return null;
    let name = raw.replace(/"/g, "");
    const colon = name.indexOf(":");
    if (colon > 0) name = name.slice(0, colon);
    name = name.toLowerCase().trim();
    return name || null;
}

function loadIconBase64(appName) {
    // Look in: custom dir (if set), then bundled icons dir
    const dirs = [];
    try {
        const cfgPath = path.join(
            __dirname,
            "..",
            "..",
            "..",
            "volume-monitor-icons-path.json",
        );
        if (fs.existsSync(cfgPath)) {
            const cfg = JSON.parse(fs.readFileSync(cfgPath, "utf8"));
            if (cfg.path) {
                // Auto-create the custom directory if it doesn't exist
                try {
                    fs.mkdirSync(cfg.path, { recursive: true });
                } catch (_) {}
                dirs.push(cfg.path);
            }
        }
    } catch (_) {}
    dirs.push(BUNDLED_ICON_DIR);

    const exts = [".png", ".jpg", ".jpeg", ".gif"];
    for (const dir of dirs) {
        for (const ext of exts) {
            try {
                const p = path.join(dir, appName + ext);
                return fs.readFileSync(p).toString("base64");
            } catch (_) {}
        }
    }
    return null;
}

class VolumeMonitorInstance extends InstanceBase {
    constructor(internal) {
        super(internal);
        this._labels = { 1: "", 2: "", 3: "", 4: "" };
        this._pollTimer = null;
    }

    async init(config) {
        this.config = config;
        this.updateFeedbacks();
        this.updatePresets();
        this._startPolling();
        this.updateStatus(InstanceStatus.Ok);
    }

    async destroy() {
        this._stopPolling();
    }

    async configUpdated(config) {
        this.config = config;
        this._stopPolling();
        this._startPolling();
        this.updateFeedbacks();
        this.updatePresets();
    }

    _startPolling() {
        this._pollTimer = setInterval(() => this._pollVariables(), 300);
    }

    _stopPolling() {
        if (this._pollTimer) {
            clearInterval(this._pollTimer);
            this._pollTimer = null;
        }
    }

    async _pollVariables() {
        for (let knob = 1; knob <= 4; knob++) {
            const raw = await this.parseVariablesInString(
                `$(custom:knob${knob}_label)`,
            );
            const label = raw || "";
            if (label !== this._labels[knob]) {
                this._labels[knob] = label;
                if (knob === 1) {
                    this.checkFeedbacks("knob_1_icon");
                } else {
                    this.checkFeedbacks(`knob_${knob}_icon`);
                }
            }
        }
    }

    getConfigFields() {
        return [
            {
                type: "static-text",
                id: "info",
                width: 12,
                value:
                    "Displays app icons on your Stream Deck+ buttons based on " +
                    "Volume Monitor's knob labels.<br /><br />" +
                    "Place custom PNG files in the module's <code>icons/</code> folder, " +
                    "named after the app (e.g. <code>floorp.png</code>).",
            },
        ];
    }

    getFeedbacks() {
        const feedbacks = {};

        feedbacks["knob_1_icon"] = {
            type: "advanced",
            name: "Show app icon for Knob 1 (Master)",
            description: "Display a speaker icon for the master volume knob",
            options: [],
            callback: () => ({ png64: loadIconBase64("generic") || "" }),
        };

        for (let knob = 2; knob <= 4; knob++) {
            const n = knob;
            feedbacks[`knob_${n}_icon`] = {
                type: "advanced",
                name: `Show app icon for Knob ${n}`,
                description: `Display the app icon for the application on knob ${n}`,
                options: [],
                callback: () => {
                    const appName = parseAppName(this._labels[n]);
                    if (!appName) return { png64: "" };

                    const b64 = loadIconBase64(appName);
                    if (b64) return { png64: b64 };

                    return { png64: loadIconBase64("generic") || "" };
                },
            };
        }

        return feedbacks;
    }

    updateFeedbacks() {
        this.setFeedbackDefinitions(this.getFeedbacks());
    }

    getPresets() {
        const presets = [];
        for (let knob = 1; knob <= 4; knob++) {
            presets.push({
                type: "button",
                category: `Knob ${knob}`,
                name: `Knob ${knob} — App Icon`,
                style: {
                    text: knob === 1 ? "MASTER VOL" : `Knob ${knob}`,
                    size: "14",
                    color: "16777215",
                    bgcolor: 0,
                },
                feedbacks: [{ feedbackId: `knob_${knob}_icon`, options: {} }],
                steps: [],
            });
        }
        return presets;
    }

    updatePresets() {
        this.setPresetDefinitions(this.getPresets());
    }
}

runEntrypoint(VolumeMonitorInstance, []);
