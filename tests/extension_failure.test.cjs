const { test } = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');

test('navigation survives backend outage, bad responses, and recovery', async () => {
    let listener;
    let mode = 'offline';
    let calls = 0;
    const errors = [];
    const logs = [];
    const context = vm.createContext({
        URL, performance,
        console: { log: (...args) => logs.push(args), error: (...args) => errors.push(args) },
        chrome: { webNavigation: { onBeforeNavigate: { addListener: fn => { listener = fn; } } } },
        fetch: async () => {
            calls++;
            if (mode === 'offline') throw new TypeError('Failed to fetch: connection refused');
            if (mode === 'http') return { ok: false, status: 503 };
            if (mode === 'json') return { ok: true, json: async () => { throw new SyntaxError('Invalid JSON'); } };
            return { ok: true, json: async () => ({ category: 'benign', is_malicious: false }) };
        },
    });
    vm.runInContext(fs.readFileSync('extension/background.js', 'utf8'), context);
    const navigate = async () => {
        assert.doesNotThrow(() => listener({ frameId: 0, url: 'https://example.test/' }));
        await new Promise(resolve => setImmediate(resolve));
    };
    for (let i = 0; i < 20; i++) await navigate();
    mode = 'http'; await navigate();
    mode = 'json'; await navigate();
    assert.equal(errors.length, 22);
    mode = 'online'; await navigate();
    assert.ok(logs.some(args => String(args[0]).startsWith('[Verdict]')));
    assert.equal(calls, 23);
    listener({ frameId: 1, url: 'https://example.test/' });
    listener({ frameId: 0, url: 'chrome://settings' });
    assert.equal(calls, 23);
});
