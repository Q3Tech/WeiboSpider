<template>
    <div>
        <div class="follow-container-head">
            <div class="form-inline">
                <div class="form-group">
                    <label>关键词</label>
                    <input type="text" class="form-control">
                    <button class="btn btn-default">跟踪</button>
                </div>
            </div>
        </div>
        <div class="follw-container-body">
            <weibo-follow v-for='keyword in keywords' v-bind:key-word="keyword"></weibo-follow>
        </div>
    </div>
</template>
<style>
    .follow-container-head {
        /*height: 50px;*/
    }
    .follw-container-body {

    }
</style>
<script>
    import WeiboFollow from './weibo-follow.vue'
    export default{
        data(){
            return{
                keywords: ['江苏 高考', '南京']
            }
        },
        components:{
            'weibo-follow':WeiboFollow
        }
    }
</script>