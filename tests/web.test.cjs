"use strict";
const assert = require("node:assert/strict");
const test = require("node:test");
globalThis.crypto = require("node:crypto").webcrypto;
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
