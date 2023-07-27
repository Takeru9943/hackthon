const apiUrl = "https://uojiroufaceapi.cognitiveservices.azure.com/";
const apiKey = "f93a32a61bb547799f3f22791746ffc9";

function displayEmotionResult(emotions) {
    const resultDiv = document.getElementById("result");
    resultDiv.innerHTML = "";

    for (const [emotion, score] of Object.entries(emotions)) {
        const emotionText = `${emotion}: ${score}`;
        resultDiv.innerHTML += `<p>${emotionText}</p>`;
    }
}

function detectEmotion() {
    const fileInput = document.getElementById("imageInput");
    const file = fileInput.files[0];

    if (!file) {
        alert("Please select an image.");
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    fetch(apiUrl, {
        method: "POST",
        headers: {
            "Ocp-Apim-Subscription-Key": apiKey,
            "Content-Type": "application/octet-stream"
        },
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.length > 0 && data[0].faceAttributes.emotion) {
            const emotions = data[0].faceAttributes.emotion;
            displayEmotionResult(emotions);
        } else {
            alert("No faces found in the image or emotion detection failed.");
        }
    })
    .catch(error => {
        console.error("Error detecting emotion:", error);
        alert("An error occurred while detecting emotion.");
    });
}
