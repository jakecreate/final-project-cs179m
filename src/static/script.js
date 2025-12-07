
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
        const data = await response.json();
        renderSystem(data);
    } catch (error) {
        console.error("Error loading grid:", error);
    }
}

async function nextStep() {
    try {
        const response = await fetch('/api/next_grid', { method: 'POST' });
        const data = await response.json();
        
        if (data.all_done) {
            document.getElementById('status-text').innerText = "OPERATION COMPLETE";
            document.getElementById('status-text').style.color = "#2ecc71";
        } else {
            renderSystem(data);
        }
    } catch (error) {
        console.error("Error advancing step:", error);
    }
}

function renderSystem(data) {
    const statusText = document.getElementById('status-text');
    statusText.innerText = `Step ${data.current_step_num} / ${data.num_steps}`;
    const gridMap = {};
    // 2. Map grid data for easy access
    data.grid.forEach(row => {
        const key = `${parseInt(row[0])},${parseInt(row[1])}`;
        gridMap[key] = row;
    });
    // 3. Render Ship Grid
    const shipContainer = document.getElementById('ship-grid');
    shipContainer.innerHTML = ''; // Clear previous
    for (let y = 8; y >= 1; y--) {
        for (let x = 1; x <= 12; x++) {
            const cellData = gridMap[`${y},${x}`];
            const cellDiv = createCell(cellData, y, x);
            shipContainer.appendChild(cellDiv);
        }
    }

    const bufferContainer = document.getElementById('buffer-grid');
    bufferContainer.innerHTML = '';
    
    for (let x = 1; x <= 4; x++) {
        const cellData = gridMap[`9,${x}`]; 
        const cellDiv = createCell(cellData, 9, x);
        if (x === 1 && data.park_cell) {
             cellDiv.classList.add(`highlight-${data.park_cell}`);
        }
        
        bufferContainer.appendChild(cellDiv);
    }
}

function createCell(cellData, y, x) {
    const div = document.createElement('div');
    div.classList.add('cell');
    if (!cellData) {
        div.classList.add('unused');
        div.innerText = "VOID";
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
    window.location.href = "/download_manifest";
}

function closeApp() {
    window.location.href = "/close";
}