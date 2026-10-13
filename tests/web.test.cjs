"use strict";
const assert = require("node:assert/strict");
const test = require("node:test");
Object.defineProperty(globalThis, "crypto", {value: require("node:crypto").webcrypto, configurable: true});
const Shamir = require("../web/shamir.js");

test("prime validation rejects composites and pseudoprimes", () => {
  assert.equal(Shamir.isPrime(2n), true);
  assert.equal(Shamir.isPrime(257n), true);
  assert.equal(Shamir.isPrime(9n), false);
  assert.equal(Shamir.isPrime(341550071728321n), false);
});

test("all threshold-size subsets reconstruct", () => {
  const output = Shamir.split("123", "3", "5", "257");
  for (let i = 0; i < output.shares.length; i++) {
    for (let j = i + 1; j < output.shares.length; j++) {
      for (let k = j + 1; k < output.shares.length; k++) {
        assert.equal(Shamir.reconstruct([output.shares[i], output.shares[j], output.shares[k]], output.prime), "123");
      }
    }
  }
});

test("auto prime and zero secret", () => {
  const output = Shamir.split("0", "2", "3");
  assert.equal(Shamir.reconstruct(output.shares.slice(0, 2), output.prime), "0");
});

test("reject composites, duplicate, alias, and invalid inputs", () => {
  assert.throws(() => Shamir.split("2", "2", "3", "9"));
  assert.throws(() => Shamir.split("2", "4", "3"));
  assert.throws(() => Shamir.split("-1", "2", "3"));
  assert.throws(() => Shamir.reconstruct([["1", "1"], ["258", "2"]], "257"));
  assert.throws(() => Shamir.reconstruct([["1", "1"], ["1", "2"]], "257"));
  assert.throws(() => Shamir.reconstruct([["1", "1"]], "257"));
});

test("browser page has valid inline JavaScript and references local runtime", () => {
  const fs = require("node:fs");
  const vm = require("node:vm");
  const path = require("node:path");
  const html = fs.readFileSync(path.join(__dirname, "../web/index.html"), "utf8");
  assert.match(html, /src="\.\/shamir\.js"/);
  const inline = html.match(/<script>([\s\S]*?)<\/script>/);
  assert.ok(inline, "inline UI script missing");
  assert.doesNotThrow(() => new vm.Script(inline[1]));
});
