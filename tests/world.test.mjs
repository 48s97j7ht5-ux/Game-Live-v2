import assert from "node:assert/strict";
import { locations, handleWorldAction } from "../js/world.js";
import { clothingLayers } from "../js/character.js";
import { apps } from "../js/phone.js";
import { formatTime, state } from "../js/state.js";

assert.equal(formatTime(490), "08:10");
assert.ok(locations.yard && locations.entrance && locations.apartment);

for (const location of Object.values(locations)) {
  assert.ok(location.place);
  assert.ok(location.actions.length >= 2);
  for (const action of location.actions) {
    const result = handleWorldAction(location.id, action.id);
    assert.equal(typeof result, "object");
  }
}

assert.equal(handleWorldAction("yard", "enter").locationId, "entrance");
assert.equal(handleWorldAction("entrance", "upstairs").locationId, "apartment");
assert.equal(handleWorldAction("apartment", "leave").locationId, "entrance");
assert.equal(state.locationId, "yard");
assert.equal(clothingLayers.length, 7);
assert.equal(apps.length, 8);

console.log("ok");
