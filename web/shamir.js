/* Self-contained educational Shamir (k,n) implementation using Web Crypto. */
"use strict";
(function (root) {
  const SMALL_PRIMES = [2n, 3n, 5n, 7n, 11n, 13n, 17n, 19n, 23n, 29n, 31n, 37n];

  function integer(value, label) {
    const input = String(value);
    if (input.length > 100) throw new Error(label + " exceeds the 100-digit input limit");
    if (!/^(0|[1-9][0-9]*)$/.test(input)) {
      throw new Error(label + " must be a non-negative decimal integer");
    }
    return BigInt(input);
  }

  function randomBelow(limit) {
    if (limit <= 0n) throw new Error("Invalid randomness bound");
    const cryptoAPI = root.crypto;
    if (!cryptoAPI || typeof cryptoAPI.getRandomValues !== "function") {
      throw new Error("Secure randomness unavailable; use HTTPS");
    }
    const bits = (limit - 1n).toString(2).length;
    const bytes = Math.ceil(bits / 8);
    const mask = (1n << BigInt(bits)) - 1n;
    const buffer = new Uint8Array(bytes);
    let value;
    do {
      cryptoAPI.getRandomValues(buffer);
      value = 0n;
      for (const byte of buffer) value = (value << 8n) + BigInt(byte);
      value &= mask;
    } while (value >= limit);
    return value;
  }

  function modPow(base, exponent, modulus) {
    let result = 1n;
    base %= modulus;
    while (exponent > 0n) {
      if (exponent & 1n) result = result * base % modulus;
      base = base * base % modulus;
      exponent >>= 1n;
    }
    return result;
  }

  function isPrime(n) {
    if (n < 2n) return false;
    for (const p of SMALL_PRIMES) {
      if (n === p) return true;
      if (n % p === 0n) return false;
    }
    let d = n - 1n, r = 0;
    while (!(d & 1n)) { d >>= 1n; r++; }
    const bases = n < (1n << 64n)
      ? [2n, 325n, 9375n, 28178n, 450775n, 9780504n, 1795265022n]
      : Array.from({length: 40}, () => randomBelow(n - 3n) + 2n);
    for (const candidate of bases) {
      const a = candidate % n;
      if (a === 0n) continue;
      let x = modPow(a, d, n);
      if (x === 1n || x === n - 1n) continue;
      let passes = false;
      for (let i = 1; i < r; i++) {
        x = x * x % n;
        if (x === n - 1n) { passes = true; break; }
      }
      if (!passes) return false;
    }
    return true;
  }

  function inverse(a, p) {
    let t = 0n, nextT = 1n, r = p, nextR = ((a % p) + p) % p;
    while (nextR !== 0n) {
      const q = r / nextR;
      [t, nextT] = [nextT, t - q * nextT];
      [r, nextR] = [nextR, r - q * nextR];
    }
    if (r !== 1n) throw new Error("Non-invertible field element");
    return (t % p + p) % p;
  }

  function split(secretInput, kInput, nInput, primeInput) {
    const secret = integer(secretInput, "Secret");
    const k = Number(integer(kInput, "Threshold"));
    const n = Number(integer(nInput, "Share count"));
    if (!Number.isSafeInteger(k) || !Number.isSafeInteger(n) ||
        k < 2 || k > n || n > 64) {
      throw new Error("Require 2 <= threshold <= share count <= 64");
    }
    if (secret.toString(2).length > 256) {
      throw new Error("Browser demonstration limits secrets to 256 bits");
    }
    let p;
    if (primeInput !== undefined && String(primeInput).trim() !== "") {
      p = integer(primeInput, "Modulus");
      if (p <= secret || p <= BigInt(n) || !isPrime(p)) {
        throw new Error("Modulus must be prime and greater than secret and share count");
      }
    } else {
      p = secret + 1n;
      if (p <= BigInt(n)) p = BigInt(n) + 1n;
      if (p < 3n) p = 3n;
      if (!(p & 1n)) p++;
      while (!isPrime(p)) p += 2n;
    }
    const coeffs = [secret];
    for (let i = 1; i < k; i++) coeffs.push(randomBelow(p));
    const shares = [];
    for (let i = 1; i <= n; i++) {
      const x = BigInt(i);
      let y = 0n;
      for (let j = coeffs.length - 1; j >= 0; j--) {
        y = (y * x + coeffs[j]) % p;
      }
      shares.push([x.toString(), y.toString()]);
    }
    return {threshold: k, num_shares: n, prime: p.toString(), shares};
  }

  function reconstruct(sharesInput, primeInput) {
    const p = integer(primeInput, "Modulus");
    if (!isPrime(p)) throw new Error("Modulus must be prime");
    if (!Array.isArray(sharesInput) || sharesInput.length < 2 || sharesInput.length > 64 || sharesInput.length >= Number(p)) {
      throw new Error("At least two and fewer than p shares are required");
    }
    const shares = sharesInput.map((share) => {
      if (!Array.isArray(share) || share.length !== 2) throw new Error("Each share must be [x,y]");
      const x = integer(share[0], "Share x"), y = integer(share[1], "Share y");
      if (x <= 0n || x >= p || y >= p) throw new Error("Non-canonical share coordinate");
      return [x, y];
    });
    if (new Set(shares.map(([x]) => x.toString())).size !== shares.length) {
      throw new Error("Duplicate share x coordinate");
    }
    let secret = 0n;
    for (let i = 0; i < shares.length; i++) {
      const [xi, yi] = shares[i];
      let numerator = 1n, denominator = 1n;
      for (let j = 0; j < shares.length; j++) {
        if (i === j) continue;
        const xj = shares[j][0];
        numerator = numerator * (p - xj) % p;
        denominator = denominator * ((xi - xj + p) % p) % p;
      }
      secret = (secret + yi * numerator * inverse(denominator, p)) % p;
    }
    return secret.toString();
  }

  const api = {split, reconstruct, isPrime, randomBelow};
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  root.ShamirDemo = api;
})(typeof globalThis !== "undefined" ? globalThis : this);
