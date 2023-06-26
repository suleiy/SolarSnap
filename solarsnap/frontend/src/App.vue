<template>
  <div id="app">
    <BannerTemplate>
       <p>
        Upload a picture of your home to see what it will look like when you add
        solar panels!
      </p>
    </BannerTemplate>
    <h3>Upload an image</h3>
      
  </div>
</template>

<script>
import BannerTemplate from "./components/Banner";
export default {
  name: "App",
  components: {
    BannerTemplate,
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