<template>
  <div id="app">
    <h1>Solar Snap <SunIcon/></h1>
      <slot />
  </div>
</template>

<script>
import SunIcon from "./SunIcon";
export default {
  name: "BannerTemplate",
  components: {
    SunIcon,
  },
};
</script>

<style>
#app {
  font-family: Avenir, Helvetica, Arial, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  text-align: center;
  color: #2c3e50;
  margin-top: 60px;
}
</style>