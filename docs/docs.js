(function () {
	var root = document.documentElement;

	document.querySelector(".theme-button").addEventListener("click", function () {
		root.classList.toggle("light-mode");
		try {
			localStorage.setItem("theme", root.classList.contains("light-mode") ? "light" : "dark");
		} catch (e) {}
	});

	document.querySelector(".menu-button").addEventListener("click", function () {
		document.body.classList.toggle("menu-open");
	});

	document.querySelector("main").addEventListener("click", function () {
		document.body.classList.remove("menu-open");
	});

	var current = document.querySelector(".chapters a.current");
	if (current)
		current.scrollIntoView({ block: "center" });

	var message = document.getElementById("message");
	var messageTimer = null;

	function showMessage(text) {
		message.textContent = text;
		message.classList.add("visible");
		clearTimeout(messageTimer);
		messageTimer = setTimeout(function () {
			message.classList.remove("visible");
		}, 1600);
	}

	document.querySelectorAll(".copy").forEach(function (button) {
		button.addEventListener("click", function () {
			var text = document.getElementById(button.dataset.copy).value;
			navigator.clipboard.writeText(text).then(function () {
				showMessage("Copied");
			}, function () {
				showMessage("Couldn't copy");
			});
		});
	});

	var links = Array.prototype.slice.call(document.querySelectorAll(".toc a"));
	var headings = links.map(function (link) {
		return document.getElementById(link.getAttribute("href").slice(1));
	});

	function updateToc() {
		var active = -1;
		for (var i = 0; i < headings.length; i++) {
			if (headings[i] && headings[i].getBoundingClientRect().top < 120)
				active = i;
		}
		links.forEach(function (link, i) {
			link.classList.toggle("active", i === active);
		});
	}

	if (links.length) {
		addEventListener("scroll", updateToc, { passive: true });
		updateToc();
	}

	var input = document.getElementById("search");
	var results = document.getElementById("search-results");
	var index = (window.searchIndex || []).map(function (entry) {
		return {
			entry: entry,
			title: entry.title.toLowerCase(),
			text: entry.text.toLowerCase()
		};
	});
	var selected = -1;

	function escape(text) {
		return text.replace(/[&<>"]/g, function (c) {
			return { "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;" }[c];
		});
	}

	function highlightTerms(text, terms) {
		var escaped = escape(text);
		terms.forEach(function (term) {
			var pattern = new RegExp("(" + term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + ")", "gi");
			escaped = escaped.replace(pattern, "<mark>$1</mark>");
		});
		return escaped;
	}

	function excerpt(text, terms) {
		var lower = text.toLowerCase();
		var at = lower.indexOf(terms[0]);
		if (at < 0)
			return text.slice(0, 160);
		var start = Math.max(0, at - 60);
		return (start > 0 ? "…" : "") + text.slice(start, start + 180);
	}

	function search() {
		var query = input.value.trim().toLowerCase();
		selected = -1;
		if (!query) {
			results.hidden = true;
			return;
		}
		var terms = query.split(/\s+/);
		var scored = [];
		index.forEach(function (item) {
			var score = 0;
			for (var i = 0; i < terms.length; i++) {
				var inTitle = item.title.indexOf(terms[i]) >= 0;
				var inText = item.text.indexOf(terms[i]) >= 0;
				if (!inTitle && !inText)
					return;
				score += (inTitle ? 10 : 0) + (inText ? 1 : 0);
			}
			if (item.title === query)
				score += 20;
			if (terms.length > 1) {
				if (item.title.indexOf(query) >= 0)
					score += 15;
				if (item.text.indexOf(query) >= 0)
					score += 5;
			}
			scored.push({ item: item, score: score });
		});
		scored.sort(function (a, b) {
			return b.score - a.score;
		});
		var html = scored.slice(0, 12).map(function (result) {
			var entry = result.item.entry;
			return "<a href=\"" + entry.url + "\"><div class=\"result-page\">" + escape(entry.page) +
				"</div><div class=\"result-title\">" + highlightTerms(entry.title, terms) +
				"</div><div class=\"result-text\">" + highlightTerms(excerpt(entry.text, terms), terms) +
				"</div></a>";
		}).join("");
		results.innerHTML = html || "<div class=\"empty\">No results</div>";
		results.hidden = false;
	}

	function move(step) {
		var items = results.querySelectorAll("a");
		if (!items.length)
			return;
		selected = (selected + step + items.length) % items.length;
		items.forEach(function (item, i) {
			item.classList.toggle("active", i === selected);
		});
		items[selected].scrollIntoView({ block: "nearest" });
	}

	input.addEventListener("input", search);
	input.addEventListener("focus", search);
	input.addEventListener("keydown", function (event) {
		if (event.key === "ArrowDown") {
			move(1);
			event.preventDefault();
		} else if (event.key === "ArrowUp") {
			move(-1);
			event.preventDefault();
		} else if (event.key === "Enter") {
			var items = results.querySelectorAll("a");
			var target = items[selected >= 0 ? selected : 0];
			if (target)
				location.href = target.href;
		} else if (event.key === "Escape") {
			results.hidden = true;
			input.blur();
		}
	});

	document.addEventListener("click", function (event) {
		if (!event.target.closest(".search"))
			results.hidden = true;
	});

	document.addEventListener("keydown", function (event) {
		if (event.key === "/" && document.activeElement !== input) {
			input.focus();
			event.preventDefault();
		}
	});
})();
