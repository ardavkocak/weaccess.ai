/* Ofis Portali - ortak arayuz davranislari (Sidebar/Header/Tema). */

/** Django CSRF cookie degerini okur (AJAX POST istekleri icin gereklidir). */
function getCsrfToken() {
    const match = document.cookie.match(/csrftoken=([^;]+)/);
    return match ? match[1] : "";
}

document.addEventListener("DOMContentLoaded", function () {
    // Sayfa icerigine hafif bir giris (fade-in) animasyonu uygula.
    const pageContent = document.querySelector(".page-content");
    if (pageContent) {
        pageContent.classList.add("fade-in-content");
    }

    // Mobilde sidebar acma/kapama.
    const toggleBtn = document.getElementById("sidebarToggle");
    const sidebar = document.getElementById("appSidebar");
    if (toggleBtn && sidebar) {
        toggleBtn.addEventListener("click", function () {
            sidebar.classList.toggle("show");
        });
    }

    // Masaustunde sidebar'i daraltma/genisletme (tercih localStorage'da saklanir).
    const collapseBtn = document.getElementById("sidebarCollapseToggle");
    const appWrapper = document.querySelector(".app-wrapper");
    if (collapseBtn && appWrapper) {
        if (localStorage.getItem("sidebarCollapsed") === "1") {
            appWrapper.classList.add("sidebar-collapsed");
        }
        collapseBtn.addEventListener("click", function () {
            appWrapper.classList.toggle("sidebar-collapsed");
            localStorage.setItem("sidebarCollapsed", appWrapper.classList.contains("sidebar-collapsed") ? "1" : "0");
        });
    }

    // Karanlik / Aydinlik tema tercihi (tum modullerde ortak).
    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeToggleIcon");
    const applyTheme = function (theme) {
        document.documentElement.setAttribute("data-theme", theme);
        if (themeIcon) {
            themeIcon.classList.toggle("bi-moon-stars", theme === "light");
            themeIcon.classList.toggle("bi-sun", theme === "dark");
        }
    };
    applyTheme(localStorage.getItem("theme") || "light");
    if (themeToggle) {
        themeToggle.addEventListener("click", function () {
            const nextTheme = document.documentElement.getAttribute("data-theme") === "dark" ? "light" : "dark";
            localStorage.setItem("theme", nextTheme);
            applyTheme(nextTheme);
        });
    }

    // Sifreyi goster/gizle (giris formu).
    document.querySelectorAll("[data-toggle-password]").forEach(function (btn) {
        btn.addEventListener("click", function () {
            const targetId = btn.getAttribute("data-toggle-password");
            const input = document.getElementById(targetId);
            if (!input) return;
            const icon = btn.querySelector("i");
            if (input.type === "password") {
                input.type = "text";
                if (icon) {
                    icon.classList.remove("bi-eye");
                    icon.classList.add("bi-eye-slash");
                }
            } else {
                input.type = "password";
                if (icon) {
                    icon.classList.remove("bi-eye-slash");
                    icon.classList.add("bi-eye");
                }
            }
        });
    });

    // Bootstrap tooltip aktivasyonu.
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(function (el) {
        new bootstrap.Tooltip(el);
    });

    // Birkac saniye sonra otomatik kaybolan basari/hata mesajlari.
    document.querySelectorAll(".alert-auto-dismiss").forEach(function (alertEl) {
        setTimeout(function () {
            const alert = bootstrap.Alert.getOrCreateInstance(alertEl);
            alert.close();
        }, 4500);
    });

    // Silme onayi gerektiren formlar/butonlar icin genel dogrulama.
    document.querySelectorAll("[data-confirm]").forEach(function (el) {
        el.addEventListener("click", function (e) {
            const message = el.getAttribute("data-confirm") || "Bu islemi yapmak istediginizden emin misiniz?";
            if (!window.confirm(message)) {
                e.preventDefault();
            }
        });
    });

    // --- Zimmet modulune ozgu davranislar (Header'daki global arama ve --
    // --- bildirim listesi, ileride baska moduller de kullanabilir). ------

    // Global canli arama (Header).
    const searchInput = document.getElementById("globalSearchInput");
    const searchResults = document.getElementById("globalSearchResults");
    if (searchInput && searchResults) {
        let debounceTimer = null;
        searchInput.addEventListener("input", function () {
            const query = searchInput.value.trim();
            clearTimeout(debounceTimer);
            if (query.length < 2) {
                searchResults.classList.remove("show");
                searchResults.innerHTML = "";
                return;
            }
            searchResults.innerHTML = '<div class="search-loading"><span class="spinner-dot"></span> Araniyor...</div>';
            searchResults.classList.add("show");

            debounceTimer = setTimeout(function () {
                fetch("/envanter/arama/?q=" + encodeURIComponent(query))
                    .then(function (response) {
                        return response.json();
                    })
                    .then(function (data) {
                        renderSearchResults(data.results);
                    })
                    .catch(function () {
                        searchResults.classList.remove("show");
                    });
            }, 250);
        });

        document.addEventListener("click", function (e) {
            if (!searchResults.contains(e.target) && e.target !== searchInput) {
                searchResults.classList.remove("show");
            }
        });

        function renderSearchResults(results) {
            if (!results || results.length === 0) {
                searchResults.innerHTML = '<div class="dropdown-item-text text-muted small px-3 py-2">Sonuc bulunamadi</div>';
                searchResults.classList.add("show");
                return;
            }
            searchResults.innerHTML = results
                .map(function (item) {
                    return (
                        '<a class="dropdown-item d-flex align-items-center gap-2 py-2" href="' + item.url + '">' +
                        '<i class="bi ' + item.icon + ' text-brand"></i>' +
                        '<span><span class="d-block small fw-semibold">' + item.title + "</span>" +
                        '<span class="d-block text-muted" style="font-size: 0.72rem;">' + item.type + " &middot; " + item.subtitle + "</span></span>" +
                        "</a>"
                    );
                })
                .join("");
            searchResults.classList.add("show");
        }
    }

    // Bildirim dropdown'undaki bir bildirime tiklaninca okundu isaretle ve yonlendir.
    document.querySelectorAll(".notification-mark-link").forEach(function (link) {
        link.addEventListener("click", function (e) {
            e.preventDefault();
            const notificationId = link.getAttribute("data-notification-id");
            const targetUrl = link.getAttribute("href");
            fetch("/envanter/bildirimler/" + notificationId + "/okundu/", {
                method: "POST",
                headers: {
                    "X-CSRFToken": getCsrfToken(),
                    "X-Requested-With": "XMLHttpRequest",
                },
            }).finally(function () {
                window.location.href = targetUrl && targetUrl !== "#" ? targetUrl : "/envanter/bildirimler/";
            });
        });
    });

    // Zimmet formu: cihaz + adet satirlarini cogaltma/kaldirma.
    const itemContainer = document.getElementById("assignmentItems");
    const addItemButton = document.getElementById("addAssignmentItem");
    const itemTemplate = document.getElementById("assignmentItemTemplate");
    if (itemContainer && addItemButton && itemTemplate) {
        const totalFormsInput = document.querySelector("input[name$='-TOTAL_FORMS']");

        // Satirlar Django formset'inin bekledigi sirayla (0,1,2...) yeniden
        // numaralandirilir; aksi halde silinen satirlar index bosluğu birakir.
        const reindex = function () {
            const rows = itemContainer.querySelectorAll(".assignment-item");
            rows.forEach(function (row, index) {
                row.querySelectorAll("input, select, textarea, label").forEach(function (el) {
                    ["name", "id", "for"].forEach(function (attr) {
                        const value = el.getAttribute(attr);
                        if (value) el.setAttribute(attr, value.replace(/-(\d+|__prefix__)-/, "-" + index + "-"));
                    });
                });
            });
            if (totalFormsInput) totalFormsInput.value = rows.length;
            // Tek satir kaldiysa silme butonu gizlenir: en az bir urun zorunlu.
            rows.forEach(function (row) {
                const removeButton = row.querySelector("[data-remove-item]");
                if (removeButton) removeButton.disabled = rows.length === 1;
            });
        };

        addItemButton.addEventListener("click", function () {
            itemContainer.appendChild(itemTemplate.content.cloneNode(true));
            reindex();
        });

        itemContainer.addEventListener("click", function (event) {
            const removeButton = event.target.closest("[data-remove-item]");
            if (!removeButton) return;
            const rows = itemContainer.querySelectorAll(".assignment-item");
            if (rows.length <= 1) return;
            removeButton.closest(".assignment-item").remove();
            reindex();
        });

        reindex();
    }
});
