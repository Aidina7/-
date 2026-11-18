/* SOC-терминал: шағын виртуалды shell (ls, cat, grep, sort, uniq, cut, wc, head, tail) және жалауды тексеру. */
(function () {
  const esc = s => String(s).replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));

  function tokenize(line) {
    const out = []; let cur = "", q = null, has = false;
    for (const ch of line) {
      if (q) { if (ch === q) q = null; else cur += ch; continue; }
      if (ch === '"' || ch === "'") { q = ch; has = true; continue; }
      if (ch === " " || ch === "\t") { if (cur || has) { out.push(cur); cur = ""; has = false; } continue; }
      if (ch === "|") { if (cur || has) { out.push(cur); cur = ""; has = false; } out.push("|"); continue; }
      cur += ch;
    }
    if (q) throw new Error("жабылмаған тырнақша");
    if (cur || has) out.push(cur);
    return out;
  }

  function lines(t) { const a = t.split("\n"); if (a[a.length - 1] === "") a.pop(); return a; }
  function joinL(a) { return a.length ? a.join("\n") + "\n" : ""; }

  function opts(args, withValue) {
    const o = {}, rest = [];
    for (let i = 0; i < args.length; i++) {
      const a = args[i];
      if (/^-\w/.test(a) && !/^-\d+$/.test(a)) {
        const letters = a.slice(1);
        for (let j = 0; j < letters.length; j++) {
          const L = letters[j];
          if (withValue.includes(L)) {
            const v = letters.slice(j + 1) || args[++i];
            if (v === undefined) throw new Error("-" + L + " үшін мән керек");
            o[L] = v; break;
          }
          o[L] = true;
        }
      } else if (/^-\d+$/.test(a)) { o.n = a.slice(1); }
      else rest.push(a);
    }
    return [o, rest];
  }

  function Shell(ch, ui) {
    this.ch = ch; this.ui = ui; this.history = []; this.hpos = 0;
  }

  Shell.prototype.read = function (name, stdin) {
    if (name === undefined) {
      if (stdin === null) throw new Error("файл атауын жазыңыз");
      return stdin;
    }
    const f = this.ch.files[name];
    if (f === undefined) throw new Error(name + ": мұндай файл жоқ (ls қараңыз)");
    return f;
  };

  Shell.prototype.cmd = function (argv, stdin) {
    const name = argv[0], args = argv.slice(1);
    const self = this;
    const C = {
      help() {
        return "Командалар:\n  ls                       файлдар тізімі\n  cat ФАЙЛ                 файлды көрсету\n  head [-n N] ФАЙЛ         алғашқы N жол (әдепкі 10)\n  tail [-n N] ФАЙЛ         соңғы N жол\n  grep [-i] [-v] [-c] ҮЛГІ [ФАЙЛ]   жолдарды іздеу (-i регистрсіз, -v керісінше, -c санау)\n  wc -l [ФАЙЛ]             жолдар саны\n  sort [-n] [-r] [-t C] [-k N]      сұрыптау (-n сан, -r кері, -t бөлгіш, -k баған)\n  uniq [-c]                қайталанбайтын жолдар (-c санымен)\n  cut -d C -f N            бағанды қию (бөлгіш C, баған N)\n  task | hint              тапсырма / кеңес\n  submit flag{...}         жауапты тексеру\n  clear                    экранды тазалау\n\nКомандаларды | арқылы біріктіруге болады:\n  grep DENY firewall.log | cut -d\" \" -f5 | sort | uniq -c | sort -n -r | head -5\n";
      },
      ls() { return Object.keys(self.ch.files).map(f => f.padEnd(18) + String(self.ch.files[f].length).padStart(8) + " байт").join("\n") + "\n"; },
      cat() { return args.length ? args.map(a => self.read(a, stdin)).join("") : self.read(undefined, stdin); },
      head() { const [o, r] = opts(args, "n"); return joinL(lines(self.read(r[0], stdin)).slice(0, +(o.n || 10))); },
      tail() { const [o, r] = opts(args, "n"); const L = lines(self.read(r[0], stdin)); return joinL(L.slice(Math.max(0, L.length - +(o.n || 10)))); },
      grep() {
        const [o, r] = opts(args, "e");
        const pat = o.e || r.shift();
        if (pat === undefined) throw new Error("grep: үлгі жоқ");
        let re;
        try { re = new RegExp(pat, o.i ? "i" : ""); } catch (e) { re = { test: s => (o.i ? s.toLowerCase().includes(pat.toLowerCase()) : s.includes(pat)) }; }
        const L = lines(self.read(r[0], stdin)).filter(l => re.test(l) !== !!o.v);
        return o.c ? L.length + "\n" : joinL(L);
      },
      wc() { const [, r] = opts(args, ""); return lines(self.read(r[0], stdin)).length + "\n"; },
      sort() {
        const [o, r] = opts(args, "tk");
        const sep = o.t, k = o.k ? parseInt(o.k, 10) : 0;
        const key = l => { if (!k) return l; const p = sep ? l.split(sep) : l.trim().split(/\s+/); return p[k - 1] || ""; };
        const L = lines(self.read(r[0], stdin)).slice();
        L.sort((a, b) => {
          const x = key(a), y = key(b);
          if (o.n) return (parseFloat(x) || 0) - (parseFloat(y) || 0);
          return x < y ? -1 : x > y ? 1 : 0;
        });
        if (o.r) L.reverse();
        return joinL(L);
      },
      uniq() {
        const [o, r] = opts(args, ""); const out = []; let prev = null, n = 0;
        lines(self.read(r[0], stdin)).concat([null]).forEach(l => {
          if (l === prev) { n++; return; }
          if (prev !== null) out.push(o.c ? String(n).padStart(7) + " " + prev : prev);
          prev = l; n = 1;
        });
        return joinL(out);
      },
      cut() {
        const [o, r] = opts(args, "df");
        if (!o.f) throw new Error("cut: -f N керек");
        const sep = o.d || "\t"; const f = o.f.split(",").map(Number);
        return joinL(lines(self.read(r[0], stdin)).map(l => { const p = l.split(sep); return f.map(i => p[i - 1] || "").join(sep); }));
      },
      task() { return self.ch.story + "\nЖауап пішімі: " + self.ch.format + "\n"; },
      hint() { self.ui.hintUsed = true; return "Кеңес: " + self.ch.hint + "\n(кеңес қолданылды: ұпай 30%-ға азаяды)\n"; },
      echo() { return args.join(" ") + "\n"; },
      pwd() { return "/home/analyst/" + self.ch.id + "\n"; },
      whoami() { return "analyst\n"; }
    };
    if (!C[name]) throw new Error(name + ": команда табылмады (help жазыңыз)");
    return C[name]();
  };

  Shell.prototype.run = async function (line) {
    const t = line.trim();
    if (!t) return "";
    this.history.push(t); this.hpos = this.history.length;
    if (t === "clear") { this.ui.clear(); return null; }
    if (t.startsWith("submit")) return this.ui.submit(t.slice(6).trim());
    const toks = tokenize(t);
    const parts = [[]];
    toks.forEach(x => { if (x === "|") parts.push([]); else parts[parts.length - 1].push(x); });
    let data = null;
    for (const p of parts) {
      if (!p.length) throw new Error("бос команда | маңында");
      data = this.cmd(p, data);
    }
    const out = data || "";
    const L = lines(out);
    return L.length > 400 ? joinL(L.slice(0, 400)) + "… (" + (L.length - 400) + " жол көрсетілмеді — head немесе grep қолданыңыз)\n" : out;
  };

  async function sha(s) {
    const b = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(s));
    return Array.from(new Uint8Array(b)).map(x => x.toString(16).padStart(2, "0")).join("");
  }

  window.mountTerminal = function (root, ch, onSolve) {
    root.innerHTML = '<div class="term"><div class="term-bar"><span></span><span></span><span></span><b>analyst@soc: ~/' + esc(ch.id) + '</b></div><div class="term-out" tabindex="0"></div><div class="term-in"><span class="ps1">$</span><input spellcheck="false" autocomplete="off" aria-label="команда"></div></div>';
    const out = root.querySelector(".term-out"), input = root.querySelector("input");
    const ui = {
      hintUsed: false, solved: false, started: Date.now(), tries: 0,
      clear() { out.innerHTML = ""; },
      async submit(flag) {
        if (!flag) return "Пайдалану: submit flag{...}\n";
        ui.tries++;
        if (await sha(flag.trim()) === ch.hash) {
          if (!ui.solved) {
            ui.solved = true;
            const secs = Math.round((Date.now() - ui.started) / 1000);
            const pts = Math.max(Math.round(ch.points * 0.3), Math.round(ch.points * (ui.hintUsed ? 0.7 : 1) - (ui.tries - 1) * 10));
            onSolve && onSolve({ points: pts, seconds: secs, hint: ui.hintUsed, tries: ui.tries });
            return "✔ ДҰРЫС! Инцидент шешілді. +" + pts + " ұпай (" + secs + " сек, әрекет: " + ui.tries + ")\n";
          }
          return "✔ Бұл челлендж шешілген.\n";
        }
        return "✘ Қате жалау. Тағы тексеріңіз (әр қате әрекет −10 ұпай).\n";
      }
    };
    const sh = new Shell(ch, ui);
    const print = (cmd, text, cls) => {
      if (cmd !== null) out.insertAdjacentHTML("beforeend", '<div><span class="ps1">$</span> ' + esc(cmd) + "</div>");
      if (text) out.insertAdjacentHTML("beforeend", '<pre class="' + (cls || "") + '">' + esc(text) + "</pre>");
      out.scrollTop = out.scrollHeight;
    };
    print(null, "SOC-терминал · челлендж: " + ch.title + "\n" + ch.story + "\n\nБастау: ls, cat README, help\n");
    input.addEventListener("keydown", async e => {
      if (e.key === "Enter") {
        const v = input.value; input.value = "";
        try { const r = await sh.run(v); if (r !== null) print(v, r, r.startsWith("✔") ? "ok" : r.startsWith("✘") ? "bad" : ""); }
        catch (err) { print(v, "қате: " + err.message + "\n", "bad"); }
      } else if (e.key === "ArrowUp") {
        if (sh.hpos > 0) { sh.hpos--; input.value = sh.history[sh.hpos]; } e.preventDefault();
      } else if (e.key === "ArrowDown") {
        if (sh.hpos < sh.history.length) { sh.hpos++; input.value = sh.history[sh.hpos] || ""; } e.preventDefault();
      } else if (e.key === "Tab") {
        e.preventDefault();
        const parts = input.value.split(" "), last = parts.pop();
        const m = Object.keys(ch.files).concat(["help", "cat", "grep", "head", "tail", "sort", "uniq", "cut", "wc", "submit", "hint", "task", "ls", "clear"]).filter(f => f.startsWith(last));
        if (m.length === 1) { parts.push(m[0]); input.value = parts.join(" "); }
      }
    });
    root.addEventListener("click", () => input.focus({ preventScroll: true }));
    return { focus: () => input.focus() };
  };
})();
