<template>
  <v-footer id="core-footer" absolute height="82">
    <div class="footer-items">
      <span v-for="link in links" :key="link.name">
        <a :href="link.Link" class="tertiary--text footer-links">{{ link.name }}</a>
      </span>
    </div>
    <v-spacer />
    <span class="font-weight-light copyright">
      &copy;
      {{ (new Date()).getFullYear() }}
      <a
        href="https://blog.g40n.xyz"
        target="_blank"
      >G40N(김가온)</a>
    </span>
  </v-footer>
</template>

<script>
export default {
  data: () => ({
    links: [
      { name: 'Home', Link: '/#' },
      { name: 'G40N', Link: 'https://github.com/gaonnr' },
      {
        name: 'Base Web Design',
        Link: 'https://creative-tim.com/presentation'
      },
      { name: 'Blog', Link: 'https://blog.g40n.xyz' }
    ]
  })
};
</script>

<style>
#core-footer {
  z-index: 0;
}
</style>
