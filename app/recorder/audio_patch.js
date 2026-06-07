(function () {
    if (window.__botRecorderActive) return;
    window.__botRecorderActive = true;

    const AC = window.AudioContext || window.webkitAudioContext;
    const actx = new AC(); // ❗ ВАЖНО: без 16kHz
    const dest = actx.createMediaStreamDestination();

    window.__chunks = [];
    window.__rec = null;

    function connect(stream) {
        if (!stream) return;
        try {
            actx.createMediaStreamSource(stream).connect(dest);
        } catch (e) {}
    }

    const OrigRTC = window.RTCPeerConnection;

    window.RTCPeerConnection = function (...args) {
        const pc = new OrigRTC(...args);

        pc.addEventListener("track", (e) => {
            if (e.track.kind !== "audio") return;

            const stream = e.streams?.[0] || new MediaStream([e.track]);
            connect(stream);

            e.track.addEventListener("unmute", () => connect(stream));
        });

        return pc;
    };

    const recorder = new MediaRecorder(dest.stream, {
        mimeType: "audio/webm;codecs=opus",
        audioBitsPerSecond: 192000
    });

    recorder.ondataavailable = (e) => {
        if (e.data.size) window.__chunks.push(e.data);
    };

    recorder.start(1000);
    window.__rec = recorder;

    console.log("[BOT] recorder ready");
})();