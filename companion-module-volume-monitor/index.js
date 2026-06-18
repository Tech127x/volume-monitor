// Volume Monitor — https://github.com/Tech127x/volume-monitor
// Created by Tech127x (https://github.com/tech127x)
// Repository: https://github.com/tech127x/volume-monitor

const {
	InstanceBase,
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
	}

	async init(config) {
		this.config = config;
		this.updateStatus(InstanceStatus.Ok);
		this.setFeedbackDefinitions(this.getFeedbacks());
		this._updatePresets();
	}

	async destroy() {
		// Nothing to clean up
	}

	async configUpdated(config) {
		this.config = config;
		this.setFeedbackDefinitions(this.getFeedbacks());
		this._updatePresets();
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

	// Build options config for the given knob number
	_getKnobFeedbackOptions(knob) {
		if (knob === 1) return [];
		return [
			{
				id: "knob_label",
				type: "textinput",
				label: `Knob ${knob} label variable`,
				description:
					`Reference to the knob ${knob} label variable, e.g. $(custom:knob${knob}_label)`,
				default: `$(custom:knob${knob}_label)`,
				useVariables: true,
			},
		];
	}

	getFeedbacks() {
		const feedbacks = {};

		feedbacks["knob_1_icon"] = {
			type: "advanced",
			name: "Show app icon for Knob 1 (Master)",
			description: "Display a speaker icon for the master volume knob",
			options: this._getKnobFeedbackOptions(1),
			affectedProperties: ["png64"],
			callback: () => ({ png64: loadIconBase64("generic") || "" }),
		};

		for (let knob = 2; knob <= 4; knob++) {
			const n = knob;
			feedbacks[`knob_${n}_icon`] = {
				type: "advanced",
				name: `Show app icon for Knob ${n}`,
				description: `Display the app icon for the application on knob ${n}`,
				options: this._getKnobFeedbackOptions(n),
				affectedProperties: ["png64"],
				callback: (feedback) => {
					const appName = parseAppName(feedback.options.knob_label);
					if (!appName) return { png64: "" };

					const b64 = loadIconBase64(appName);
					if (b64) return { png64: b64 };

					return { png64: loadIconBase64("generic") || "" };
				},
			};
		}

		return feedbacks;
	}

	_getPresetsStructure() {
		return [
			{
				id: "volume-monitor-icons",
				name: "Volume Monitor",
				description: "App icon presets for Stream Deck+ knobs",
				definitions: ["knob_1_icon", "knob_2_icon", "knob_3_icon", "knob_4_icon"],
			},
		];
	}

	_getPresetDefinitions() {
		return {
			knob_1_icon: {
				type: "simple",
				name: "Knob 1 — Master Volume Icon",
				style: {
					text: "MASTER VOL",
					size: "14",
					color: "16777215",
					bgcolor: 0,
				},
				feedbacks: [{ feedbackId: "knob_1_icon", options: {} }],
				steps: [],
			},
			knob_2_icon: {
				type: "simple",
				name: "Knob 2 — App Icon",
				style: {
					text: "Knob 2",
					size: "14",
					color: "16777215",
					bgcolor: 0,
				},
				feedbacks: [{ feedbackId: "knob_2_icon", options: {} }],
				steps: [],
			},
			knob_3_icon: {
				type: "simple",
				name: "Knob 3 — App Icon",
				style: {
					text: "Knob 3",
					size: "14",
					color: "16777215",
					bgcolor: 0,
				},
				feedbacks: [{ feedbackId: "knob_3_icon", options: {} }],
				steps: [],
			},
			knob_4_icon: {
				type: "simple",
				name: "Knob 4 — App Icon",
				style: {
					text: "Knob 4",
					size: "14",
					color: "16777215",
					bgcolor: 0,
				},
				feedbacks: [{ feedbackId: "knob_4_icon", options: {} }],
				steps: [],
			},
		};
	}

	_updatePresets() {
		this.setPresetDefinitions(
			this._getPresetsStructure(),
			this._getPresetDefinitions(),
		);
	}
}

module.exports = VolumeMonitorInstance;
