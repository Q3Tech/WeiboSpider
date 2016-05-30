<template>
    <div>
        <!-- main view -->
        <nav class="navbar navbar navbar-default navbar-fixed-top">
            <div class="navbar-header">
                <a class="navbar-brand" href="#!/">WeiboFollow</a>
                <button type="button" class="navbar-toggle collapsed pull-right" data-toggle="collapse" data-target=".navbar-collapse">
                    <span class="sr-only">展开</span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                    <span class="icon-bar"></span>
                </button>

            </div>
            <div class="navbar-collapse collapse">
            <ul class="nav navbar-nav">
                <li><a href="#!/wordfollow/">关键词跟踪</a></li>
                <li><a href="#!/wordfollow-control/">关键词跟踪控制</a></li>
            </ul>
            <div class="navbar-form">
                <input type="text" class="form-control" v-model="inputKeyword" placeholder="关键词">
                <button class="btn btn-default" v-on:click="addKeyword">跟踪</button>
            </div>
        </nav>
        <router-view
            class="view"
            keep-alive
            transition
            transition-mode="out-in">
        </router-view>
    </div>
</template>
<style>
    .view {
        padding-top: 50px;
        height:100%;
    }
</style>
<script>
    export default{
        data(){
            return {
                inputKeyword: ""
            }
        },
        methods: {
            addKeyword: function(){
                this.$broadcast('container-add-keyword', this.inputKeyword);
            }
        }
    }
</script>
