<template>
  <v-container fill-height fluid grid-list-xl>
    <v-layout wrap>
      <v-flex xs12>
        <h3>{{ username }}</h3>
      </v-flex>
      <v-flex sm6 xs12 md6 lg3>
        <material-stats-card
          color="pink"
          icon="mdi-upload"
          title="Debt"
          :value="`${debt}₩`"
          sub-icon="mdi-calendar"
          sub-text="Since beginning"
        />
      </v-flex>
      <v-flex sm6 xs12 md6 lg3>
        <material-stats-card
          color="blue"
          icon="mdi-download"
          title="Credit"
          :value="`${credit}₩`"
          sub-icon="mdi-calendar"
          sub-text="Since beginning"
        />
      </v-flex>
      <v-flex md12 lg12>
        <material-card color="pink" title="Debts" text="돈을 제때제때 갚읍시다">
          <v-data-table :headers="debtHeaders" :items="debts" hide-actions>
            <template slot="headerCell" slot-scope="{ header }">
              <span
                class="font-weight-light text-warning text--darken-3"
                v-text="header.text"
              />
            </template>
            <template slot="items" slot-scope="{ index, item }">
              <td class="text-xs-right">{{ item.no }}</td>
              <td>{{ item.content }}</td>
              <td>
                <router-link :to="`/user-profile?uid=${item.eul_uid}`">{{
                  item.creditor
                }}</router-link>
              </td>
              <td class="text-xs-right">{{ item.reduce_price }}</td>
              <td class="text-xs-right">{{ item.date }}</td>
              <td>{{ item.account }}</td>
            </template>
          </v-data-table>
        </material-card>
      </v-flex>
      <v-flex md12 lg12>
        <material-card
          color="blue"
          title="Credits"
          text="돈을 제때제때 갚읍시다"
        >
          <v-data-table :headers="creditHeaders" :items="credits" hide-actions>
            <template slot="headerCell" slot-scope="{ header }">
              <span
                class="font-weight-light text-warning text--darken-3"
                v-text="header.text"
              />
            </template>
            <template slot="items" slot-scope="{ index, item }">
              <td class="text-xs-right">{{ item.no }}</td>
              <td>{{ item.content }}</td>
              <td>
                <router-link :to="`/user-profile?uid=${item.gab_uid}`">{{
                  item.debtor
                }}</router-link>
              </td>
              <td class="text-xs-right">{{ item.reduce_price }}</td>
              <td class="text-xs-right">{{ item.date }}</td>
            </template>
          </v-data-table>
        </material-card>
      </v-flex>
    </v-layout>
  </v-container>
</template>

<script>
export default {
  data() {
    return {
      randomTitles: [
        '마왕',
        '피보다 붉은자',
        '이세계로 전생한',
        '양털을 잘 깎는',
        '드래곤 슬레이어',
        '쥬니어네이버 마스터',
        '삼도수군통제사',
        '감귤포장학과 석좌교수',
        '독타',
        '78수생'
      ],
      username: undefined,
      debt: 0,
      credit: 0,
      creditHeaders: [
        {
          sortable: false,
          text: '#',
          value: 'tid',
          align: 'right'
        },
        {
          sortable: false,
          text: '항목',
          value: 'name'
        },
        {
          sortable: false,
          text: '줄놈',
          value: 'debtor'
        },
        {
          sortable: false,
          text: '금액',
          value: 'price',
          align: 'right'
        },
        {
          sortable: true,
          text: '날짜',
          value: 'date',
          align: 'right'
        }
      ],
      debtHeaders: [
        {
          sortable: false,
          text: '#',
          value: 'tid',
          align: 'right'
        },
        {
          sortable: false,
          text: '항목',
          value: 'name'
        },
        {
          sortable: false,
          text: '받을놈',
          value: 'creditor'
        },
        {
          sortable: false,
          text: '금액',
          value: 'price',
          align: 'right'
        },
        {
          sortable: true,
          text: '날짜',
          value: 'date',
          align: 'right'
        },
        {
          sortable: false,
          text: '계좌',
          value: 'account'
        }
      ],
      credits: [],
      debts: []
    };
  },
  methods: {
    getUsername() {
      let title = this.randomTitles[
        Math.floor(this.randomTitles.length * Math.random())
      ];
      this.$http.get(`/api/user?uid=${this.$route.query.uid}`).then(res => {
        this.username = `[${title}] ${res.data.nick} (${res.data.name})`;
      });
    },
    getDebts() {
      return this.$http
        .get(`/api/trade?did=${this.$route.query.uid}`)
        .then(res => {
          this.debt = res.data.reduce(
            (total, obj) => obj.reduce_price + total,
            0
          );
          return res.data;
        })
        .catch(err => {
          console.log(err);
        });
    },
    getCredits() {
      return this.$http
        .get(`/api/trade?cid=${this.$route.query.uid}`)
        .then(res => {
          this.credit = res.data.reduce(
            (total, obj) => obj.reduce_price + total,
            0
          );
          return res.data;
        })
        .catch(err => {
          console.log(err);
        });
    },
    preprocess(raws, processed) {
      console.log(raws);
      raws.forEach((el, idx) => {
        this.$http
          .get(`/api/user?uid=${el.eul_uid}`)
          .then(res => {
            el.creditor = res.data.nick;
            return el;
          })
          .then(el => {
            this.$http
              .get(`/api/user?uid=${el.gab_uid}`)
              .then(res => {
                el.debtor = res.data.nick;
                return el;
              })
              .then(el => {
                processed.push(el);
                processed.sort((a, b) => Number(b.no) - Number(a.no));
                // TODO: optimization
              });
          })
          .catch(err => {
            return err;
          });
      });
    }
  },
  mounted() {
    this.getUsername();
    this.getDebts().then(data => this.preprocess(data, this.debts));
    this.getCredits().then(data => this.preprocess(data, this.credits));
  }
};
</script>
