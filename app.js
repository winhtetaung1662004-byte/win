// JSON data from your Outline server or static file
const API_URL = "https://raw.githubusercontent.com/winhtetaung1662004-byte/win/main/Key.json");
async function loadKeys() {
  const container = document.getElementById("keys");
  container.innerHTML = "Loading...";
  try {
    const res = await fetch(API_URL);
    const data = await res.json();
    container.innerHTML = "";
    data.forEach(k => {
      const div = document.createElement("div");
      div.className = "key";
      div.innerHTML = `
        <h3>${k.name}</h3>
        <p>Server: ${k.server}</p>
        <textarea readonly style="width:100%;height:60px">${k.accessKey}</textarea>
        <br>
        <button onclick="copyKey('${k.accessKey}')">Copy</button>
      `;
      container.appendChild(div);
    });
  } catch (err) {
    container.innerHTML = "Error loading keys: " + err;
  }
}

function copyKey(key) {
  navigator.clipboard.writeText(key);
  alert("Copied: " + key);
}

loadKeys();
