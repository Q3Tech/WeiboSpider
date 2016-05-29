<template>
    <div class="wordfollow-control">
        <table class="table">
            <thead>
            <th>关键词</th>
            <th>运行状态</th>
            <th>最近一次爬取</th>
            <th>爬取间隔</th>
            </thead>
            <tbody>
            <tr v-for="wf in wordfollowers">
                <td>{{ wf.word }}</td>
                <td>{{ wf.running }}</td>
                <td>{{ wf.time_text }}</td>
                <td>{{ wf.interval }}</td>
            </tr>
            </tbody>
        </table>
    </div>
</template>
<style>

</style>
<script>
//    import HeaderComponent from './components/header.vue'
//    import OtherComponent from './components/other.vue'
    var $ = require("jquery")
    var dateFormat = require('dateformat');
    export default{
        data(){
            return{
                wordfollowers_raw: []
            }
        },
        computed: {
            wordfollowers:function(){
                var wordfollowers = [];
                for (var i = 0; i < this.wordfollowers_raw.length; i++){
                    var t = this.wordfollowers_raw[i];
                    wordfollowers.push({
                        word: t.word,
                        running: t.running,
                        time_text: dateFormat(new Date(t.newest_timestamp),"yyyy-mm-dd hh:MM:ss"),
                        interval: t.interval
                    });
                }
                return wordfollowers;
            }
        },
        methods: {
          load: function(callback) {
              var self = this;
              console.log("hehe");
              $.getJSON('/api/wordfollow/' , function(data){
                  self.wordfollowers_raw=data;
                  callback();
              });
          }
        },
        route: {
            activate: function (transition) {
                console.log('wordfollow-control activated!')
                this.load(function () {
                    transition.next()
                })
            },
            deactivate: function (transition) {
                console.log('wordfollow-control deactivated!')
                transition.next()
            }
        }
    }
</script>