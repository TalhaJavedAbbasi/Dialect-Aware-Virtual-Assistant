document.addEventListener("DOMContentLoaded", function () {
    fetch("/api/mood-trends")
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                console.error("Error fetching mood data:", data.error);
                return;
            }

            // Extract mood trends
            const moodTrends = data.mood_trends;
            const dominantMood = data.dominant_mood;
            document.getElementById("dominantMood").innerText = `Dominant Mood: ${dominantMood}`;

            // Extract labels (dates) and data for charts
            const labels = Object.keys(moodTrends);
            const happyData = labels.map(date => moodTrends[date].Happy || 0);
            const sadData = labels.map(date => moodTrends[date].Sad || 0);
            const frustratedData = labels.map(date => moodTrends[date].Frustrated || 0);

            // Call chart functions
            renderCharts(labels, happyData, sadData, frustratedData);
        })
        .catch(error => console.error("Error loading mood trends:", error));
});

function renderCharts(labels, happyData, sadData, frustratedData) {
    const chartOptions = {
        responsive: true,
        maintainAspectRatio: false,
        scales: {
            y: {
                beginAtZero: true,
                title: { display: true, text: "Mood Count" }
            },
            x: {
                title: { display: true, text: "Date" }
            }
        },
        plugins: {
            legend: { display: true, position: "top" },
            tooltip: { enabled: true }
        }
    };

    new Chart(document.getElementById("moodTrendChart").getContext("2d"), {
        type: "line",
        data: {
            labels: labels,
            datasets: [
                { label: "Happy 😊", data: happyData, borderColor: "green", fill: false },
                { label: "Sad 😢", data: sadData, borderColor: "blue", fill: false },
                { label: "Frustrated 😡", data: frustratedData, borderColor: "red", fill: false }
            ]
        },
        options: chartOptions
    });

    new Chart(document.getElementById("moodBarChart").getContext("2d"), {
        type: "bar",
        data: {
            labels: labels,
            datasets: [
                { label: "Happy 😊", data: happyData, backgroundColor: "green" },
                { label: "Sad 😢", data: sadData, backgroundColor: "blue" },
                { label: "Frustrated 😡", data: frustratedData, backgroundColor: "red" }
            ]
        },
        options: chartOptions
    });

    new Chart(document.getElementById("moodPieChart").getContext("2d"), {
        type: "pie",
        data: {
            labels: ["Happy 😊", "Sad 😢", "Frustrated 😡"],
            datasets: [{
                data: [
                    happyData.reduce((a, b) => a + b, 0),
                    sadData.reduce((a, b) => a + b, 0),
                    frustratedData.reduce((a, b) => a + b, 0)
                ],
                backgroundColor: ["green", "blue", "red"]
            }]
        },
        options: chartOptions
    });
}
