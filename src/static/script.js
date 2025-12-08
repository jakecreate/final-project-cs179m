let stepHistory = [];

document.addEventListener('DOMContentLoaded', () => {
    fetchGridState();
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            nextStep();
        }
    });
});

async function fetchGridState() {
    try {
        const response = await fetch('/api/current_grid');
        const data = await response.json(); //data is the main way to get all the info about the grid
        renderSystem(data);
        StepHistory(data);
        const timeElement = document.getElementById('time-display');
        timeElement.innerText = data.total_time;
        const steps = document.getElementById('steps-display');
        steps.innerText = data.num_steps;
    } catch (error) {
        console.error("Error loading grid:", error);
    }
}

async function nextStep() {
    try {
        const response = await fetch('/api/next_grid', { method: 'POST' });
        const data = await response.json();
        
        StepHistory(data);
        renderSystem(data);
    } catch (error) {
        console.error("Error advancing step:", error);
    }
}

function renderStepLog() {
    const container = document.getElementById('step-log');
    if (!container) 
        return;

    container.innerHTML = '';

    if (stepHistory.length === 0) {
        container.innerHTML = `<div class="text-gray-400 text-center text-sm py-4">No steps taken yet. Press "Next Step" to begin.</div>`;
        return;
    }

    stepHistory.forEach((msg) => {
        const item = document.createElement('div');
        item.className = 'step-log-item';
        item.innerHTML = msg;
        container.appendChild(item);
    });

    container.scrollTop = container.scrollHeight;
}
function StepHistory(data) {
    stepHistory = [];
    if (!data || !data.steps || data.steps.length === 0) {
        renderStepLog();
        return;
    }
    let completedCount = data.current_step_num + 1;
    if(completedCount > data.steps.length) {
        completedCount = data.steps.length;
    }
    if (data.all_done) {
        completedCount = data.steps.length;
    }

    for (let idx = 0; idx < completedCount; idx++) {
        const step = data.steps[idx];
        //const costs = data.costs[idx];
        //const time = String(costs).padStart(2, '0');
        const fromY = String(step[0]).padStart(2, '0');
        const fromX = String(step[1]).padStart(2, '0');
        const toY = String(step[2]).padStart(2, '0');
        const toX = String(step[3]).padStart(2, '0');
        const fromLabel = (fromY === '09' && fromX === '01') ? 'park' : `[${fromY},${fromX}]`;
        const toLabel = (toY === '09' && toX === '01') ? 'park' : `[${toY},${toX}]`;

        const isMove = idx % 2 === 1; //moving a container are odd
        const stepNum = idx + 1;
        const totalSteps = data.num_steps;
        const fromSpan = `<span style="color: #2ecc71; font-weight: bold;">${fromLabel}</span>`;
        const toSpan = `<span style="color: #e74c3c; font-weight: bold;">${toLabel}</span>`;

        let message = '';
        if (isMove) {
             message = `${stepNum} of ${totalSteps}: Move from ${fromSpan} to ${toSpan}`;
            //message = `${stepNum} of ${totalSteps}: Move from ${fromSpan} to ${toSpan} and it takes, ${time} minutes`;
        } else {
            message = `${stepNum} of ${totalSteps}: Move crane from ${fromSpan} to ${toSpan}`;
            //message = `${stepNum} of ${totalSteps}: Move crane from ${fromSpan} to ${toSpan} and it takes, ${time} minutes`;
        }

        if (stepHistory.length === 0 || stepHistory[stepHistory.length - 1] !== message) {
            stepHistory.push(message);
        }
    }

    renderStepLog();
}
//create the grid in its entirety
function renderSystem(data) {
    const statusText = document.getElementById('status-text');
    if (data.all_done) {
        statusText.innerText = "OPERATION DONE";
        statusText.style.color = "#2ecc71";
    } else {
        statusText.innerText = `Step ${data.current_step_num} / ${data.num_steps}`;
        statusText.style.color = "";
    }
    
    const gridMap = {};
    data.grid.forEach(row => {
        const key = `${parseInt(row[0])},${parseInt(row[1])}`;
        gridMap[key] = row;
    });
    
    const shipContainer = document.getElementById('ship-grid');
    shipContainer.innerHTML = '';
    for (let y = 8; y >= 1; y--) {
        for (let x = 1; x <= 12; x++) {
            const cellData = gridMap[`${y},${x}`];
            const cellDiv = createCell(cellData, y, x);
            shipContainer.appendChild(cellDiv);
        }
    }

    const bufferContainer = document.getElementById('buffer-grid');
    bufferContainer.innerHTML = '';
    
    const cellData = gridMap[`9,1`]; 
    const cellDiv = createCell(cellData, 9, 1);
    if (data.park_cell) {
        cellDiv.classList.add(`highlight-${data.park_cell}`);
    }
    
    bufferContainer.appendChild(cellDiv);
}
//look at each Cell and determine the information
function createCell(cellData, y, x) {
    const div = document.createElement('div');
    div.classList.add('cell');
    if (!cellData) {
        div.classList.add('unused');
        div.innerText = " ";
        return div;
    }
    const weight = cellData[2];
    const name = cellData[3];
    const color = cellData[4]; 
    if (name === "NAN") {
        div.classList.add('nan');
        div.innerText = "NAN";
    } else if (name === "UNUSED") {
        div.classList.add('unused');
    } else {
        div.classList.add('container');
        const displayWeight = parseInt(weight, 10) || weight;
        div.innerHTML = `<span>${name.substring(0, 5)}</span><small>${displayWeight}</small>`;
    }

    if (color === 'red') {
        div.classList.add('highlight-red');
    } else if (color === 'green') {
        div.classList.add('highlight-green');
    }

    return div;
}

function downloadManifest() {
    const updateStatus = document.getElementById('update-status');
    window.location.href = "/download_manifest";
    if(updateStatus) {
        updateStatus.innerText = "Done! file was written to the desktop";
    }
}

function closeApp() {
    window.location.href = "/close";
}