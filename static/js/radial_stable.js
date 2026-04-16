const items = document.querySelectorAll(".item");
const panel = document.getElementById("panel");
const center = document.querySelector(".center");

let activeType = null;

const data = {
    koruma: {
        title: "Spam Koruma",
        desc: "Canlı koruma ve filtreleme ekranına geçiş yapar."
    },
    analiz: {
        title: "SMS Analizi",
        desc: "Mesaj analizi ve spam skorlarının olduğu alana geçiş yapar."
    },
    engel: {
        title: "Engellenenler",
        desc: "Engellenen numaralar ve kara liste alanına geçiş yapar."
    },
    bildirim: {
        title: "Bildirimler",
        desc: "Uyarılar ve sistem bildirimlerinin olduğu bölüme geçiş yapar."
    },
    topluluk: {
        title: "Topluluk",
        desc: "Topluluk verileri ve ortak spam kayıtlarının olduğu bölüme geçiş yapar."
    },
    ayarlar: {
        title: "Ayarlar",
        desc: "Uygulama ayarları ekranına geçiş yapar."
    }
};

function animateCenter() {
    center.classList.remove("center-react");
    void center.offsetWidth;
    center.classList.add("center-react");
}

function renderPanel(type) {
    const item = data[type];
    if (!item) return;

    panel.classList.remove("panel-show");
    void panel.offsetWidth;

    panel.innerHTML = `
        <h2>${item.title}</h2>
        <p>${item.desc}</p>
    `;

    panel.classList.add("panel-show");
}

items.forEach((btn) => {
    btn.addEventListener("click", () => {
        const type = btn.dataset.type;
        const url = btn.dataset.url;

        if (activeType === type) {
            window.location.href = url;
            return;
        }

        activeType = type;

        items.forEach(x => x.classList.remove("active"));
        btn.classList.add("active");

        animateCenter();
        renderPanel(type);
    });
});
