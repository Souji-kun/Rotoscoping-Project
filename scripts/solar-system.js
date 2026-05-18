/* jshint esversion: 6, browser: true */

(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', () => {
  const planetOrbitalPeriods = {
    mercury: 0.24,
    venus: 0.62,
    earth: 1,
    mars: 1.88,
    jupiter: 11.86,
    saturn: 29.46,
    uranus: 84.01,
    neptune: 164.8,
    pluto: 248.6
  };

  function calculatePlanetAges() {
    const ageInput = document.getElementById('earthAge');
    const feedback = document.getElementById('ageCalculatorFeedback');

    if (!ageInput || !feedback) {
      return;
    }

    const earthAge = Number.parseFloat(ageInput.value);

    if (!Number.isFinite(earthAge) || earthAge <= 0) {
      feedback.textContent = 'Please enter a valid age greater than zero.';
      return;
    }

    feedback.textContent = 'Your solar system age comparison is ready.';

    Object.entries(planetOrbitalPeriods).forEach(([planet, orbitalPeriod]) => {
      const result = (earthAge / orbitalPeriod).toFixed(2);
      const resultNode = document.getElementById(`${planet}-age`);
      if (resultNode) {
        resultNode.textContent = `${result} years`;
      }
    });
  }

  const calculateBtn = document.getElementById('calculatePlanetAges');
  const ageInputEl = document.getElementById('earthAge');

  if (calculateBtn) {
    calculateBtn.addEventListener('click', calculatePlanetAges);
  }

  if (ageInputEl) {
    ageInputEl.addEventListener('keydown', (event) => {
      if (event.key === 'Enter') {
        calculatePlanetAges();
      }
    });
  }
  });
}());
