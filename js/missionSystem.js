// js/missionSystem.js - 미션 시스템
const MISSIONS = [
    { id: 1, text: '🟢 초록불이 켜졌어요!', instruction: '📱 흔들어줘', type: 'shake' },
    { id: 2, text: '👀 좌우를 살펴봐!', instruction: '📱 흔들어줘', type: 'shake' },
    { id: 3, text: '👁️ 좌우 회전하며 살피기', instruction: '🔄 회전해줘', type: 'rotate' },
    { id: 4, text: '✅ 다 건넜어!', instruction: '📱 흔들어줘', type: 'shake' }
];

let mission = { active: false, currentIndex: 0, detecting: false };
let lastGamma = 0;

export function startMission(crosswalk) {
    if (mission.active) return;
    
    mission.active = true;
    mission.currentIndex = 0;
    mission.detecting = true;
    
    const missionPanel = document.getElementById('mission-panel');
    if (missionPanel) missionPanel.classList.add('active');
    
    updateMissionUI();
    startGyroDetection();
}

export function updateMissionUI() {
    if (!mission.active) return;
    
    const currentM = MISSIONS[mission.currentIndex];
    if (!currentM) {
        completeMission();
        return;
    }
    
    document.getElementById('mission-current').textContent = currentM.id;
    document.getElementById('mission-text').textContent = currentM.text;
    document.getElementById('mission-instruction').textContent = currentM.instruction;
    document.getElementById('mission-progress').style.width = `${((mission.currentIndex + 1) / MISSIONS.length) * 100}%`;
    document.getElementById('mission-status').textContent = '미션을 수행해주세요!';
}

export function completeMission() {
    mission.active = false;
    mission.detecting = false;
    stopGyroDetection();
    
    const missionPanel = document.getElementById('mission-panel');
    const missionStatus = document.getElementById('mission-status');
    
    if (missionStatus) missionStatus.textContent = '미션 완료! 🎉';
    if (missionPanel) missionPanel.classList.remove('active');
    
    if ('vibrate' in navigator) navigator.vibrate([500, 200, 500]);
}

function missionSuccess() {
    mission.currentIndex++;
    
    if (mission.currentIndex >= MISSIONS.length) {
        completeMission();
        return;
    }
    
    const missionStatus = document.getElementById('mission-status');
    const missionPanel = document.getElementById('mission-panel');
    
    if (missionStatus) missionStatus.textContent = '잘했어요! 🎉';
    if (missionPanel) missionPanel.classList.add('mission-success');
    
    setTimeout(() => {
        if (missionPanel) missionPanel.classList.remove('mission-success');
        updateMissionUI();
    }, 1500);
}

export function startGyroDetection() {
    window.addEventListener('devicemotion', handleShake);
    window.addEventListener('deviceorientation', handleRotate);
}

export function stopGyroDetection() {
    mission.detecting = false;
    window.removeEventListener('devicemotion', handleShake);
    window.removeEventListener('deviceorientation', handleRotate);
}

function handleShake(event) {
    if (!mission.active || !mission.detecting) return;
    
    const currentM = MISSIONS[mission.currentIndex];
    if (!currentM || currentM.type !== 'shake') return;
    
    const acc = event.acceleration;
    if (!acc) return;
    
    if (Math.abs(acc.x || 0) > 15) {
        missionSuccess();
    }
}

function handleRotate(event) {
    if (!mission.active || !mission.detecting) return;
    
    const currentM = MISSIONS[mission.currentIndex];
    if (!currentM || currentM.type !== 'rotate') return;
    
    const gamma = event.gamma || 0;
    if (lastGamma !== 0 && Math.abs(gamma - lastGamma) > 20) {
        missionSuccess();
    }
    lastGamma = gamma;
}