<template>
  <v-container fill-height fluid grid-list-xl>
    <v-layout wrap>
      <v-flex sm6 xs12 md6 lg4>
        <material-stats-card
          color="orange"
          icon="mdi-square-inc-cash"
          title="Total Debt"
          :value="`${totalDebt}₩`"
          sub-icon="mdi-calendar"
          sub-text="Since beginning"
        />
      </v-flex>
      <!--
      <v-flex md12 lg12>
        <material-chart-card></material-chart-card>
      </v-flex>
      -->
      <v-flex md12 lg12>
        <material-card color="red" :title="`최근 ${rec}건의 거래`" text="유지보수 지원자 받습니다.">
          <v-data-table :headers="headers" :items="debts" hide-actions>
            <template slot="headerCell" slot-scope="{ header }">
              <span class="font-weight-light text-warning text--darken-3" v-text="header.text" />
            </template>
            <template slot="items" slot-scope="{ index, item }">
              <td class="text-xs-right">{{ item.no }}</td>
              <td>{{ item.content }}</td>
              <td>
                <router-link :to="`/user-profile?uid=${item.gab_uid}`">
                  {{
                  item.debtor
                  }}
                </router-link>
              </td>
              <td>
                <router-link :to="`/user-profile?uid=${item.eul_uid}`">
                  {{
                  item.creditor
                  }}
                </router-link>
              </td>
              <td class="text-xs-right">{{ item.reduce_price }}</td>
              <td class="text-xs-right">{{ item.date }}</td>
              <td>{{ item.account }}</td>
            </template>
          </v-data-table>
          <p style="text-align: center;" v-on:click="getMore">더보기</p>
        </material-card>
      </v-flex>
      <v-flex md6 lg6>
        <material-card color="green" title="호갱 랭킹" text="호-호-">
          <v-data-table :headers="statHeaders" :items="topCreditors" hide-actions>
            <template slot="headerCell" slot-scope="{ header }">
              <span class="font-weght-light text-warning text--darken-3" v-text="header.text"></span>
            </template>
            <template slot="items" slot-scope="{ index, item }">
              <td class="text-xs-right">{{ index + 1 }}</td>
              <td>
                <router-link :to="`/user-profile?uid=${item.uid}`">
                  {{
                  item.nick
                  }}
                </router-link>
              </td>
              <td class="text-xs-right">{{ item.sum }}</td>
            </template>
          </v-data-table>
        </material-card>
      </v-flex>
      <v-flex md6 lg6>
        <material-card color="purple" title="나쁜놈 랭킹" text="제발 좀 갚아!!!">
          <v-data-table :headers="statHeaders" :items="topDebtors" hide-actions>
            <template slot="headerCell" slot-scope="{ header }">
              <span class="font-weght-light text-warning text--darken-3" v-text="header.text"></span>
            </template>
            <template slot="items" slot-scope="{ index, item }">
              <td class="text-xs-right">{{ index + 1 }}</td>
              <td>
                <router-link :to="`/user-profile?uid=${item.uid}`">
                  {{
                  item.nick
                  }}
                </router-link>
              </td>
              <td class="text-xs-right">{{ item.sum }}</td>
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
      totalDebt: 0,
      rec: 5,
      headers: [
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
          sortable: false,
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
      debts: [],
      statHeaders: [
        {
          sortable: false,
          text: '순위',
          value: 'num',
          align: 'right'
        },
        {
          sortable: false,
          text: '닉네임',
          value: 'nickname'
        },
        {
          sortable: false,
          text: '금액',
          value: 'amount',
          align: 'right'
        }
      ],
      topCreditors: [],
      topDebtors: []
    };
  },
  methods: {
    getTotalDebt() {
      this.$http
        .get('/api/trade')
        .then(res => {
          this.totalDebt = res.data;
        })
        .catch(err => {
          console.log(err);
        });
    },
    getRecentTrades() {
      return this.$http
        .get(`/api/trade?rec=${this.rec}`)
        .then(res => {
          return res.data;
        })
        .catch(err => {
          console.log(err);
        });
    },
    getTops(type, cnum) {
      return this.$http
        .get(`/api/stats?${type}num=${cnum}`)
        .then(res => res.data)
        .catch(err => console.log(err));
    },
    preprocess(rawDebts) {
      rawDebts.forEach((el, idx) => {
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
                this.debts.push(el);
                this.debts.sort((a, b) => Number(b.no) - Number(a.no));
                // TODO: optimization
              });
          })
          .catch(err => {
            return err;
          });
      });
    },
    preprocessStats(rawStats, arg) {
      rawStats.forEach((el, idx) => {
        this.$http
          .get(`/api/user?uid=${el.uid}`)
          .then(res => {
            el.nick = res.data.nick;
            return el;
          })
          .then(el => {
            arg.push(el);
            arg.sort((a, b) => Number(b.sum) - Number(a.sum));
          })
          .catch(err => err);
      });
    },
    getMore(event) {
      this.rec += 5;
      this.getRecentTrades().then(data => this.preprocess(data));
    },
    reload() {
      this.getTotalDebt();
      this.getRecentTrades().then(data => this.preprocess(data));
      this.getTops('c', 10).then(data =>
        this.preprocessStats(data, this.topCreditors)
      );
      this.getTops('d', 10).then(data =>
        this.preprocessStats(data, this.topDebtors)
      );
    }
  },
  mounted() {
    this.reload();
  }
};
</script>
