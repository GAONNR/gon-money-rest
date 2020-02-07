<template>
  <v-toolbar id="core-toolbar" app flat prominent style="background: #eee;">
    <div class="v-toolbar-title">
      <v-toolbar-title class="tertiary--text font-weight-light">
        <v-btn v-if="responsive" class="default v-btn--simple" dark icon @click.stop="onClickBtn">
          <v-icon>mdi-view-list</v-icon>
        </v-btn>
        {{ title }}
      </v-toolbar-title>
    </div>

    <v-spacer />
    <v-toolbar-items>
      <v-flex align-center layout py-2>
        <v-text-field
          class="mr-4 purple-input"
          label="Search..."
          hide-details
          color="purple"
          v-model="nickInput"
          v-on:keyup.enter="search"
        />
      </v-flex>
    </v-toolbar-items>
  </v-toolbar>
</template>

<script>
import { mapMutations } from 'vuex';

export default {
  data: () => ({
    title: null,
    responsive: false,
    users: {},
    nickInput: ''
  }),

  watch: {
    $route(val) {
      this.title = val.name;
    }
  },

  mounted() {
    this.onResponsiveInverted();
    window.addEventListener('resize', this.onResponsiveInverted);
    this.getUsers();
  },
  beforeDestroy() {
    window.removeEventListener('resize', this.onResponsiveInverted);
  },

  methods: {
    ...mapMutations('app', ['setDrawer', 'toggleDrawer']),
    onClickBtn() {
      this.setDrawer(!this.$store.state.app.drawer);
    },
    onClick() {
      //
    },
    onResponsiveInverted() {
      if (window.innerWidth < 991) {
        this.responsive = true;
      } else {
        this.responsive = false;
      }
    },
    getUsers() {
      this.$http
        .get('/api/user')
        .then(res => {
          res.data.forEach(e => {
            this.users[e.nick] = e;
          });
        })
        .catch(err => console.log(err));
    },
    search() {
      if (this.nickInput in this.users) {
        this.$router.push(
          `/user-profile?uid=${this.users[this.nickInput].uid}`
        );
      } else {
        alert(`닉네임 ${this.nickInput}이(가) 없습니다.`);
      }
    }
  }
};
</script>

<style>
#core-toolbar a {
  text-decoration: none;
}
</style>
